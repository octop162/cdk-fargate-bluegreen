from typing import Protocol
from attr import attr
from aws_cdk.aws_autoscaling import HealthCheck
from constructs import Construct
from aws_cdk import (
    CfnCodeDeployBlueGreenAdditionalOptions,
    CfnCodeDeployBlueGreenApplication,
    CfnCodeDeployBlueGreenApplicationTarget,
    CfnCodeDeployBlueGreenEcsAttributes,
    CfnCodeDeployBlueGreenHook,
    CfnTrafficRoutingConfig,
    CfnTrafficRoutingTimeBasedCanary,
    CfnTrafficRoutingType,
    CfnTrafficRouting,
    CfnTrafficRoute,
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_ecr as ecr,
    aws_ecs as ecs,
)
from settings.constant import Constant


class ContainerStack(Stack):

    def __init__(
            self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        '''
        リソース取得
        '''
        vpc = ec2.Vpc.from_lookup(self, 'Vpc',
                                  vpc_id=Constant.VPC_ID
                                  )
        ecr_repo = ecr.Repository.from_repository_name(
            self,
            "Repository",
            repository_name=Constant.REPOSITORY_NAME,
        )

        '''
        ロードバランサ
        '''
        # ロードバランサ本体
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "ApplicationLoadBalancer",
            vpc=vpc,
            internet_facing=True,
        )

        # ターゲットグループ(テスト用に2つ用意)
        target_group1 = elbv2.ApplicationTargetGroup(
            self,
            "TargetGroup1",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            vpc=vpc,
            deregistration_delay=Duration.seconds(60),
            health_check=elbv2.HealthCheck(
                enabled=True,
                interval=Duration.seconds(30),
                path='/',
                protocol=elbv2.Protocol.HTTP,
                healthy_http_codes='200',
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
                timeout=Duration.seconds(10),
            )
        )
        target_group2 = elbv2.ApplicationTargetGroup(
            self,
            "TargetGroup2",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            vpc=vpc,
            deregistration_delay=Duration.seconds(60),
            health_check=elbv2.HealthCheck(
                enabled=True,
                interval=Duration.seconds(30),
                path='/',
                protocol=elbv2.Protocol.HTTP,
                healthy_http_codes='200',
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
                timeout=Duration.seconds(10),
            )
        )

        # リスナー作成(テスト用に2つ用意)
        main_listener = alb.add_listener(
            "MainListener",
            port=80,
            open=True,
            default_action=elbv2.ListenerAction.weighted_forward(
                [
                    elbv2.WeightedTargetGroup(
                        target_group=target_group1,
                        weight=100,
                    )
                ]
            )
        )
        test_listener = alb.add_listener(
            "TestListener",
            port=8080,
            open=True,
            default_action=elbv2.ListenerAction.weighted_forward(
                [
                    elbv2.WeightedTargetGroup(
                        target_group=target_group1,
                        weight=100,
                    )
                ]
            )
        )

        '''
        ECS
        '''
        # ECSクラスタ
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc, cluster_name='Cluster')
        service_security_group = ec2.SecurityGroup(
            self, 'ServiceSecurtyGroup',
            vpc=vpc,
        )
        service_security_group.connections.allow_from(
            alb,
            ec2.Port.tcp(80),
        )

        # ECSタスク定義
        task_definition = ecs.FargateTaskDefinition(
            self, "TaskDef",
            memory_limit_mib=512,
            cpu=256,)
        container = task_definition.add_container(
            "Container",
            image=ecs.ContainerImage.from_ecr_repository(ecr_repo),
            memory_limit_mib=256,
        )
        container.add_port_mappings(
            ecs.PortMapping(
                container_port=80,
                protocol=ecs.Protocol.TCP,
            )
        )

        # ECSサービス
        service = ecs.CfnService(
            self, "Service",
            cluster=cluster.cluster_name,
            desired_count=1,
            deployment_controller=ecs.CfnService.DeploymentControllerProperty(
                type="EXTERNAL"
            ),
            propagate_tags="SERVICE"
        )
        service.node.add_dependency(target_group1)
        service.node.add_dependency(target_group2)
        service.node.add_dependency(main_listener)
        service.node.add_dependency(test_listener)

        # タスクセット
        task_set = ecs.CfnTaskSet(
            self,
            'TaskSet',
            cluster=cluster.cluster_name,
            service=service.attr_name,
            scale=ecs.CfnTaskSet.ScaleProperty(
                unit="PERCENT", value=100,
            ),
            task_definition=task_definition.task_definition_arn,
            launch_type="FARGATE",
            load_balancers=[
                ecs.CfnTaskSet.LoadBalancerProperty(
                    container_name=task_definition.default_container.container_name,
                    container_port=task_definition.default_container.container_port,
                    target_group_arn=target_group1.target_group_arn,
                )
            ],
            network_configuration=ecs.CfnTaskSet.NetworkConfigurationProperty(
                aws_vpc_configuration=ecs.CfnTaskSet.AwsVpcConfigurationProperty(
                    subnets=vpc.select_subnets(
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT).subnet_ids,
                    assign_public_ip="DISABLED",
                    security_groups=[
                        service_security_group.security_group_id,
                    ]
                )
            )
        )
        ecs.CfnPrimaryTaskSet(
            self,
            'PrimaryTaskSet',
            cluster=cluster.cluster_name,
            service=service.attr_name,
            task_set_id=task_set.attr_id,
        )

        '''
        Blue Greenデプロイメント
        '''
        self.add_transform('AWS::CodeDeployBlueGreen')
        task_definition_logical_id = self.get_logical_id(
            task_definition.node.default_child)
        task_set_logical_id = self.get_logical_id(task_set)
        CfnCodeDeployBlueGreenHook(
            self, "CodeDeployBlueGreenHook",
            traffic_routing_config=CfnTrafficRoutingConfig(
                type=CfnTrafficRoutingType.TIME_BASED_CANARY,
                time_based_canary=CfnTrafficRoutingTimeBasedCanary(
                    step_percentage=20,
                    bake_time_mins=15,
                ),
            ),
            additional_options=CfnCodeDeployBlueGreenAdditionalOptions(
                termination_wait_time_in_minutes=30,
            ),
            service_role=Constant.IAM_BLUEGREEN_DEPLOYMENT_SERVICE_ROLE_NAME,
            applications=[
                CfnCodeDeployBlueGreenApplication(
                    target=CfnCodeDeployBlueGreenApplicationTarget(
                        type=service.cfn_resource_type,
                        logical_id=self.get_logical_id(service),
                    ),
                    ecs_attributes=CfnCodeDeployBlueGreenEcsAttributes(
                        task_definitions=[
                            task_definition_logical_id,
                            task_definition_logical_id + "Green",
                        ],
                        task_sets=[
                            task_set_logical_id,
                            task_set_logical_id + "Green",
                        ],
                        traffic_routing=CfnTrafficRouting(
                            prod_traffic_route=CfnTrafficRoute(
                                type=elbv2.CfnListener.CFN_RESOURCE_TYPE_NAME,
                                logical_id=self.get_logical_id(
                                    main_listener.node.default_child),
                            ),
                            test_traffic_route=CfnTrafficRoute(
                                type=elbv2.CfnListener.CFN_RESOURCE_TYPE_NAME,
                                logical_id=self.get_logical_id(
                                    test_listener.node.default_child),
                            ),
                            target_groups=[
                                self.get_logical_id(
                                    target_group1.node.default_child),
                                self.get_logical_id(
                                    target_group2.node.default_child),
                            ]
                        )
                    )
                )
            ]
        )
