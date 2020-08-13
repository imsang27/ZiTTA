const Discord = require(`discord.js`); // discord.js를 불러옴
const client = new Discord.Client(); // 새로운 디스코드 클라이언트를 만듬
const token = process.env.token;
//const config = require('./config.json');
//const { prefix, token } = require('./config.json');

// 만약에 클라이언트가 준비되었다면, 아래의코드를 실행합니다
// 이 이벤트는 봇이 로그인 되고 한번만 실행될것입니다
client.once('ready', () => {
  console.log("ZiTTA 봇이 온라인 상태 입니다!");
});

/*----------msg = ping, send = pong----------*/
client.on('message', message => {
    if (message.content === "!ping" ) {
        // "Pong"으로 되돌려 칩니다.
        message.channel.send("Pong");
    }
  });
/***-------------------------------------------***/

// 여러분의 디스코드 토큰으로 디스코드에 로그인합니다
client.login(token);
