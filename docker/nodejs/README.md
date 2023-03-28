# NODEJS

## PART 1 - The docker image

### Create NodeJS docker files

Create package,json by running

```bash
npm init -y
npm install express
```

### Create docker image and run app.js

```bash
docker build -t <image-name> .
docker -d run -p 3000:3000 node-app <image-name>
```

open Browser [node-app](http://localhost:3000)
