from flask import Flask, jsonify
import tinytuya
import os

app = Flask(__name__)

DEVICE_ID = os.environ.get("TUYA_DEVICE_ID")
IP = os.environ.get("TUYA_DEVICE_IP")
LOCAL_KEY = os.environ.get("TUYA_LOCAL_KEY")
VERSION = float(os.environ.get("TUYA_VERSION", "3.3"))

if not all([DEVICE_ID, IP, LOCAL_KEY]):
    raise RuntimeError("Missing required environment variables")

d = tinytuya.OutletDevice(
    dev_id=DEVICE_ID,
    address=IP,
    local_key=LOCAL_KEY
)

d.set_version(VERSION)


def get_current_state():
    try:
        status = d.status()
        return status["dps"]["1"]
    except Exception:
        return None


@app.route("/health")
def health():
    state = get_current_state()

    return jsonify({
        "device_reachable": state is not None,
        "state": state
    })


@app.route("/set/<state>")
def set_state(state):

    desired = state.lower() == "on"

    current = get_current_state()

    if current is None:
        return jsonify({
            "changed": False,
            "error": "device_unreachable"
        })

    if current == desired:
        return jsonify({
            "changed": False,
            "state": "no_change"
        })

    try:
        d.set_status(desired)

        return jsonify({
            "changed": True,
            "state": "updated"
        })

    except Exception as e:
        return jsonify({
            "changed": False,
            "error": str(e)
        })


@app.route("/toggle")
def toggle():

    current = get_current_state()

    if current is None:
        return jsonify({
            "changed": False,
            "error": "device_unreachable"
        })

    try:
        d.set_status(not current)

        return jsonify({
            "changed": True,
            "state": "toggled"
        })

    except Exception as e:
        return jsonify({
            "changed": False,
            "error": str(e)
        })


if __name__ == "__main__":
    HOST = os.environ.get("TUYA_API_HOST", "127.0.0.1")
    PORT = int(os.environ.get("TUYA_API_PORT", "5000"))

    app.run(host=HOST, port=PORT)