# Flask-Matomo-D

![](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)
[![PyPI](https://img.shields.io/pypi/v/flask-matomo-d.svg?style=flat-square&colorB=dfb317)](https://pypi.org/project/flask-matomo-d/)

Flask-Matomo-D is a library which lets you track the requests of your Flask website using Matomo (Piwik).

## Installation

```
pip install flask-matomo-d
```

## Usage

```python
from flask import Flask, render_template
from flask_matomo import *

app = Flask(__name__)
matomo = Matomo(app,
                matomo_url="https://matomo.mydomain.com",
                id_site=5,
                token_auth="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                secure=True,
                allowed_paths=None)

@app.route("/")
def index():
  return render_template("index.html")

if __name__ == "__main__":
  app.run()
```

In the code above:

1. The *Matomo* object is created by passing in the Flask application and arguments to configure Matomo.
2. The *matomo_url* parameter is the url to your Matomo installation.
3. The *id_site* parameter is the id of your site. This is used if you track several websites with on Matomo installation. It can be found if you open your Matomo dashboard, change to site you want to track and look for &idSite= in the url.
4. The *token_auth* parameter can be found in the area API in the settings of Matomo. It is required for tracking the ip address.
5. The *secure* parameter indicates whether the verification of trusted certificates is performed, by default is True.
6. The *allowed_paths* indicates allowed paths of every incoming request to be tracked, use regex sintax. Ex: 'dasd|paht1|admin'

## Meta

Lucas Hild - [https://lucas-hild.de](https://lucas.hild.de)
This project is licensed under the MIT License - see the LICENSE file for details
