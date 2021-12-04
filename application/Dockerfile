FROM nginx

COPY ./default.conf /etc/nginx/conf.d/default.conf
COPY ./public /root/public

RUN mkdir /root/logs
RUN chmod 755 -R /root

CMD [ "nginx", "-g", "daemon off;" ]