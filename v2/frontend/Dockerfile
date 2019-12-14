FROM node:alpine AS modules

ADD ./package.json /app/package.json
ADD ./yarn.lock /app/yarn.lock

WORKDIR /app
RUN yarn install

# Development - watches files
FROM node:alpine AS dev

ADD ./ /app
COPY --from=modules /app/node_modules /app/node_modules

WORKDIR /app

CMD yarn install && yarn dev

# Production
FROM node:alpine AS prod

COPY --from=dev /app /app

WORKDIR /app
RUN yarn build

CMD yarn start
