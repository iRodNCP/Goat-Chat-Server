# Goat Chat Private Server

To set this up run
```
    pip install sanic
```
Then copy Goat Chat's [mediaserver](https://drive.google.com/drive/folders/1XvLtcmut0nkk3_W77RoX2T2l-sadhfH6) to /www/goat.

add this to your nginx config
```
    location ~ ^/goat/(.*).php$ {
        proxy_pass http://localhost:8000/goat/$1$is_args$args;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
```
run the server by running
```
    python3 goat.py
```
