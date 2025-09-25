# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/KPandaK/metaeditor_safetensors/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                          |    Stmts |     Miss |   Cover |   Missing |
|-------------------------------------------------------------- | -------: | -------: | ------: | --------: |
| metaeditor\_safetensors/layouts/about\_ui\_layout.py          |      188 |      188 |      0% |     1-360 |
| metaeditor\_safetensors/layouts/main\_ui\_layout.py           |      216 |      216 |      0% |     1-510 |
| metaeditor\_safetensors/layouts/thumbnail\_ui\_layout.py      |       14 |       14 |      0% |      1-22 |
| metaeditor\_safetensors/models/metadata.py                    |       53 |        1 |     98% |        41 |
| metaeditor\_safetensors/models/settings.py                    |       11 |        0 |    100% |           |
| metaeditor\_safetensors/models/theme.py                       |       75 |        0 |    100% |           |
| metaeditor\_safetensors/services/config\_service.py           |       74 |        1 |     99% |        22 |
| metaeditor\_safetensors/services/model\_detection\_service.py |       72 |        6 |     92% |51-55, 100-101, 127 |
| metaeditor\_safetensors/services/safetensors\_service.py      |      130 |        9 |     93% |119, 138-141, 150, 185, 214-215 |
| metaeditor\_safetensors/services/save\_worker.py              |       20 |        0 |    100% |           |
| metaeditor\_safetensors/services/theme\_service.py            |      190 |       23 |     88% |76, 84, 143-144, 224-226, 244-246, 251, 270-280, 288-289, 295-296 |
| metaeditor\_safetensors/services/utility.py                   |       69 |        2 |     97% |    64, 99 |
| metaeditor\_safetensors/views/about\_dialog.py                |       53 |       53 |      0% |      1-87 |
| metaeditor\_safetensors/views/main\_view.py                   |      176 |      176 |      0% |     1-265 |
| metaeditor\_safetensors/views/settings\_dialog.py             |      165 |      165 |      0% |     1-303 |
| metaeditor\_safetensors/views/thumbnail\_dialog.py            |       18 |       18 |      0% |      1-31 |
|                                                     **TOTAL** | **1524** |  **872** | **43%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/KPandaK/metaeditor_safetensors/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/KPandaK/metaeditor_safetensors/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/KPandaK/metaeditor_safetensors/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/KPandaK/metaeditor_safetensors/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FKPandaK%2Fmetaeditor_safetensors%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/KPandaK/metaeditor_safetensors/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.