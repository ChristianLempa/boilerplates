const express = require ('express')
const app = express()

app.get('/', (req, res) => res.send('Hello From NodeJS World!'))
app.listen(3000, () => console.log('servers running'))