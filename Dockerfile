FROM python:2.7
MAINTAINER skyscraper <skyscraper@xianda.com>
ENV TZ=Asia/Shanghai
RUN mkdir -p /code
RUN mkdir -p /logs
ADD . /code
WORKDIR /code

RUN pip install -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com
RUN chmod +x start_service.sh
EXPOSE 58482

CMD ["./start_service.sh"]
