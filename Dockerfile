ARG SRC_IMAGE
ARG SRC_TAG

FROM ${SRC_IMAGE}:${SRC_TAG}

WORKDIR /tmp/build
# Copy dependencies
COPY requirements.lock .
# Install dependencies
RUN pip install --no-deps --target ${LAMBDA_TASK_ROOT} -r requirements.lock

WORKDIR ${LAMBDA_TASK_ROOT}
# Copy source code
COPY app/ .
# Point to lambda handler
CMD [ "lambda_handler.handle"]
