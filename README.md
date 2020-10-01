# ifmo-xblock-ant

XBlock for edx-platfrom implementing interconnection between Open edX and AcademicNT.

## Requirements

XBlock is compatible with the 9-th openEdx named release _Ironwood_, and most likely in not compatible with any other.

Add the following line in `requirements.txt`:

```
-e git+https://github.com/openeduITMO/ifmo-edx-celery-grader@v4.0#egg=ifmo-edx-celery-grader==4.0
-e git+https://github.com/openeduITMO/ifmo-xblock-ant@v4.1#egg=ifmo-xblock-ant==4.1
```

## Installation

Add following parameters in `lms.env.json`:

```javascript
"XBLOCK_SETTINGS": {
    "IFMO_XBLOCK_ANT": {
        "SELECTED_CONFIGURATION": "selected_configuration",
        "ATTEMPTS_URL": "attempts_url_goes_here",
        "LAB_URL": "lab_url_goes_here",
        "REGISTER_URL": "register_url_goes_here",
        "COURSE_INFO": "course_info_url_goes_here"
    }
}
```

Add following apps in `INSTALLED_APPS`:

```python
INSTALLED_APPS += (
    "ifmo_celery_grader",
    "xblock_ant",
)
```

Or modify `lms.env.json` and `cms.env.json`:
 
```javascript
"ADDL_INSTALLED_APPS": [
    "ifmo_celery_grader",
    "xblock_ant"
]
```

Package `ifmo_celery_grader` uses **migrations**.

## Configuration

`SELECTED_CONFIGURATION` can now be `ifmo`, `npoed` or `default`.

`ATTEMPTS_URL` is optional, may be omitted when `SELECTED_CONFIGURATION` is either 
`ifmo` or `npoed` otherwise unpredicted behaviour may occur.

`LAB_URL` is optional, may be omitted when `SELECTED_CONFIGURATION` is either 
`ifmo` or `npoed` otherwise unpredicted behaviour may occur.

`REGISTER_URL` is optional, may be omitted.

`COURSE_INFO` is optional, may be omitted when `SELECTED_CONFIGURATION` is either 
`ifmo` or `npoed` otherwise unpredicted behaviour may occur.

## Deployment

Sample for `server_vars.yml`:

```yml
XBLOCK_SETTINGS:
    IFMO_XBLOCK_ANT:
        SELECTED_CONFIGURATION: "selected_configuration_goes_here"
        "ATTEMPTS_URL": "attempts_url_goes_here"
        "LAB_URL": "lab_url_goes_here"
        "REGISTER_URL": "register_url_goes_here"
        "COURSE_INFO": "course_info_url_goes_here"
```

## Usage

XBlock provides entry point `ifmo_xblock_ant` which must be used in course **Advanced settings**.
