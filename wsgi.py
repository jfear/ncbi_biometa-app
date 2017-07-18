#!/usr/bin/env python
from app import create_app

app = create_app('app.config.ProdConfig')

if __name__ == "__main__":
    app.run()
