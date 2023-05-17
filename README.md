# Flask-Matomo

![](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)
[![PyPI](https://img.shields.io/pypi/v/flask-matomo2.svg?style=flat-square&colorB=dfb317)](https://pypi.org/project/flask-matomo2/)
<!-- [![Docs](https://img.shields.io/badge/docs-readthedocs-red.svg?style=flat-square)](https://flask-matomo.readthedocs.io) -->

Flask-Matomo is a library which lets you track the requests of your Flask website using Matomo (Piwik).

Forked from [LucasHild/flask-matomo](https://github.com/LucasHild/flask-matomo).
## Installation

```
pip install flask-matomo
```

## Usage

```python
from flask import Flask, jsonify
from flask_matomo import *

app = Flask(__name__)
matomo = Matomo(app, matomo_url="https://matomo.mydomain.com",
                id_site=5, token_auth="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

@app.route("/")
def index():
  return jsonify({"page": "index"})

if __name__ == "__main__":
  app.run()
```

In the code above:

1. The *Matomo* object is created by passing in the Flask application and arguments to configure Matomo.
2. The *matomo_url* parameter is the url to your Matomo installation.
3. The *id_site* parameter is the id of your site. This is used if you track several websites with one Matomo installation. It can be found if you open your Matomo dashboard, change to site you want to track and look for &idSite= in the url.
4. The *token_auth* parameter can be found in the area API in the settings of Matomo. It is required for tracking the ip address.


### Adding details to route

You can provide details to a route in 2 ways, first by using the `matomo.details` decorator:

```python
from flask import Flask, render_template
from flask_matomo import *

app = Flask(__name__)
matomo = Matomo(app, matomo_url="https://matomo.mydomain.com",
                id_site=5, token_auth="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

@app.route("/foo")
@matomo.details(action_name="Foo")
def index():
  return render_template("index.html")

if __name__ == "__main__":
  app.run()
```

or by giving details to the Matomo constructor:
```python
from flask import Flask, render_template
from flask_matomo import *

app = Flask(__name__)
matomo = Matomo(
  app,
  matomo_url="https://matomo.mydomain.com",
  id_site=5,
  token_auth="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  routes_details={
    "/foo": {
      "action_name": "Foo"
    }
  }
)

@app.route("/foo")
def index():
  return render_template("index.html")

if __name__ == "__main__":
  app.run()
```

## Meta

Lucas Hild - [https://lucas-hild.de](https://lucas.hild.de)
This project is licensed under the MIT License - see the LICENSE file for details

# Release Notes

## Latest Changes


### Changed

- Track original IP address if request was forwarded by proxy. [Tanikai/flask-matomo](https://github.com/Tanikai/flask-matomo) by [@Tanakai](https://github.com/Tanakai).
- Change ignored routes to compare against rules instead of endpoint. [MSU-Libraries](https://github.com/MSU-Libraries/flask-matomo) by [@meganschanz](https://github.com/meganschanz).
- Add ignored UserAgent prefix; set action to be url_rule. [MSU-Libraries](https://github.com/MSU-Libraries/flask-matomo) by [@natecollins](https://github.com/natecollins).
- Fix matomo.ignore decorator.


## 0.1.0

- Forked from [LucasHild/flask-matomo](https://github.com/LucasHild/flask-matomo).
- Renamed to `flask-matomo2`.
- Add test suite.
- Setup CI with Github Actions.
