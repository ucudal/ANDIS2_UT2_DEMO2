import http from 'k6/http';
import { sleep } from 'k6';

export let options = {
  stages: [
    { duration: '15s', target: 10 },  // 10 usuarios durante 15s
    { duration: '15s', target: 50 },  // 50 usuarios durante 15s
    { duration: '15s', target: 100 }, // 100 usuarios durante 15s
    { duration: '15s', target: 0 },   // bajada
  ],
};

export default function () {
  http.get('http://localhost:8080/orders/user/1');
  sleep(0.01);
}
