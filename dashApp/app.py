from dash import Dash, dcc, html, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
import dash_daq as daq
import smtplib
import imaplib
import email
from email.header import decode_header
import threading
import Freenove_DHT as DHT
import asyncio
# import Mqtt_Reader as MQTT
# import rfid.rfid_read as RFID
import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime
import time
import sqlite3
import bluetooth
import re

global dht_temp
global dht_humidity
global mqtt_light
global can_send_email
global waiting_on_response
global fan_state
global rfid_id
global bluetooth_device_count
global can_send_light_email
global tempThreshold
global user_email
global temp_email_alert
global months 
global send_signed_in_email

profileChangeSwitch = False
dht_temp = 0
dht_humidity = 0
mqtt_light = 0
can_send_email = True
waiting_on_response = False
fan_state = "fanOff"
bluetooth_device_count = 0
rfid_id = None
can_send_light_email = False
tempThreshold = None
user_email = None
temp_email_alert = False
send_signed_in_email = False

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# List all pins for sensor (James)
sensor_pins = [18]
led_pin = 13
sensor_data = dict.fromkeys(["temperature", "humidity", "light"], None)

motor_pins = [22, 27, 17]
GPIO.setup(motor_pins[0],GPIO.OUT)
GPIO.setup(motor_pins[1],GPIO.OUT)
GPIO.setup(motor_pins[2],GPIO.OUT)

GPIO.setup(led_pin,GPIO.OUT)

sender_email = "testvanier@gmail.com"
# receiver_email = "testvanier@gmail.com"
password = "hmpz ofwn qxfn byjq"

app = Dash(__name__)

theme = {
    'dark': True,
    'detail': '#007439',
    'primary': '#00EA64',
    'secondary': '#6E6E6E',
}

app.layout = html.Div([
    html.Link(rel="stylesheet", href="style.css"),
    html.Link(rel="preconnect", href="https://fonts.googleapis.com"),
    html.Link(rel="preconnect", href="https://fonts.gstatic.com"),
    html.Link(href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,300;0,400;0,600;0,700;1,300&display=swap", rel="stylesheet"),
    html.Script(src="assets/script.js"),
    html.Script(src="assets/pureknob.js"),
    dcc.Interval(id="dht_light_thread_interval", interval=1000),
    dcc.Store(id='loaded-user-profile', storage_type='session'),
    # User preference section
    html.Div(className="container", id="profile", children=[
        html.Div(className="container", id="profileDiv1", children=[
            html.Div(id="profilepiccontainer", children=[
            html.Img(src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAPFBMVEXk5ueutLepsLPo6uursbXJzc/p6+zj5ea2u76orrKvtbi0ubzZ3N3O0dPAxcfg4uPMz9HU19i8wcPDx8qKXtGiAAAFTElEQVR4nO2d3XqzIAyAhUD916L3f6+f1m7tVvtNINFg8x5tZ32fQAIoMcsEQRAEQRAEQRAEQRAEQRAEQRAEQRAEQRAEQRAEQTghAJD1jWtnXJPP/54IgNzZQulSmxvTH6oYXX4WS+ivhTbqBa1r26cvCdCu6i0YXbdZ0o4A1rzV+5IcE3YE+z58T45lqo7g1Aa/JY5tgoqQF3qb382x7lNzBLcxft+O17QUYfQI4IIeklKsPSN4i6LKj/7Zm8n99RbHJpEw9gEBXNBpKIYLJqKYRwjOikf//r+J8ZsVuacbqCMNleI9TqGLGqMzhnVdBOdd6F/RlrFijiCoVMk320CBIahUxTWI0KKEcJqKbMdpdJb5QvdHq6wCI5qhKlgGMS/RBHkubWDAE+QZxB4xhCyDiDkLZxgGEVdQldzSKbTIhmZkFkSEPcVvmBn2SMuZB9od7fQDsMiDdKJjFUSCQarM5WirZ3C2TT/htYnyPcPfgrFHWz0BI74gr6J/IZiGUxAZGQLqmvQLTrtE/Go4YxhVRIpEw+sww1IIcqr5NKmUUzLF3d4/qPkYIp2T/obPuemlojFUR4t9Q2Vojhb7BmgElWHzLPH8hucfpefPNFTVgs9h1AdU/Pin96vwWbWdf+X9Absn3OdO34aMdsDnP8WgKYisTqI6CkNGqZQo1XA6Ef6AU32SJzOcBukHPF07/xNSgmHKa5BOhtezv6mA/rYJpwXNAnbRZ1XuF3BzDcO3vpA3+ny2909gbqE4hhD3LIPhLLyBNhPZvbZ3B+3tPYa18A7auSlXQayKwTPNLKDcuOB0xPYKDPFTkWsevQPRZ1J8Hji9I1KQ34r7hZhrwNwOZ97QxNx0drwn4QI0wQk1DcEsfKCWKdxVvxPSNUIp/knmAXT+nT+Ko3+0H96rcNb3m1fx7MBTJdeBJ7uFcWsc0wvgAsC4pROW0l2inbAmIBv/7GZmuhQH6API2rr8T0e6yuZJ+80A9LZeG62T3tik31XwxtwZcizKuTHkMjB1WdZde4Kmic/A5ZI3rr1ae21d08PlVHYfAaxw9G9CYRbJ+8ZdbTcMRV1XM3VdF0M32vtoTdZ0+u29s0OttJ5bz64UwinjaFMVY9vkqc3KKSxN21Xl+0L4Q3Vuv1tYl0pqnX6ms4XetFz7gdZVAgUEoJntfOUe4ZwsHd9FzqQ3Vv6xe41l0XJcqcKl6TZvlv7ClAW3BsqQW4X7ypApB8dmTgK4IX5wvqIVj33HtD2qSG4BqznxdIefL27Y4sahi0MdIdvUsDva8agGGbCtITmCY31MHD2O0uIdh/0rJDQ1VX5Zdxz3rR2QDbv6qXl9vudzqQtGm1Jv9LDXOsfvvB7VcZ8PDKD0mQ1VHPYQ9O+Yj4hR1IUD8rBnn3ho2m8oQMxbCFiKlL2ioSW5heeJqegED52CzxCtcGD3Kv8Wms9EYLyUhwaFIhSMBClevWEmiK/Iaogu4H7sg6ppQhQG8RUqivuTGOAJOg6FfgW0q0M0PQMRMEgXaeNf3SYDZ8PIMI0+wHgr/MgN7wYwpiLjCCqM6ydUDZLQiB6nDdNC8SDyig3jPPpFXGcC9O8BUBDVmgBY59E7Md/35Loe/UVEECEJwYggJjELZ4J71SaQSBeC02n4Da29CayJNA28SAhd2CQyC1Xw6pSmGSINQVuMhAZp4DClan9MgmkDDNmezqwS8sgtlXK/EPBhoaSmYVC/F7IO1jQEdHOlabpKh3+jzLQSTUiq4X2I+Ip/zU8rlaqAvkS21ElR+gqu3zbjjL+hIAiCIAiCIAiCIAiCsCf/AKrfVhSbvA+DAAAAAElFTkSuQmCC", 
            id="profilepic"),
            html.Div(id="profilepicedit", children=[
                html.Img(id="whitePencilImg", src=app.get_asset_url("images/white_pencil.png"))
            ]),
            dbc.Modal(
                [
                dbc.ModalBody(id="modal-content", children=[
                    html.Div(style={"width": "100%", "height": "100%", "display": "flex", "justify-content": "center", "align-items": "center"}, children=[
                        html.Div(style={"margin-top": "20px", "width": "50%:", "border": "5px solid #222222", "border-radius": "20px", "background-color": "#525252", "display": "flex", "flex-direction": "column", "justify-content": "center", "align-items": "stretch"}, children=[
                            html.H4(style={"margin": "10px"}, children="Enter link to new profile picture"),
                            dcc.Input(value="idk", id="pfp_src_input", style={"margin": "0px 10px", "background-color": "transparent", "border": "none"}),
                            html.Div(style={"display": "flex", "justify-content": "center", "align-items": "center"}, children=[
                                html.Button(id="savePfpBtn", style={"margin": "10px"}, children="Save"),
                                html.Button(id="closePopupBtn", style={"margin": "10px"}, children="Close")
                            ])
                        ])
                    ])
                ]),
            ],
            id="modal", className="container-fluid", style={"position": "absolute", "width": "100%", "height": "100%", "background-color": "rgba(0, 0, 0, 0.5)", "top": "0", "left": "0"}
            )
            ]),
        ]),
        html.Div(className="container", id="profileDiv2", children=[
            html.H5(style={"font-style": "italic"}, children="Welcome"),
            dcc.Input(type="text", style={"font-size": "42pt", "font-weight": "bold"}, value="<Username>", id="nameInput"),
            dcc.Input(type="text", value="<Email>", id="emailInput")
        ]),
        html.Div(className="container", id="profileDiv3", children=[
            html.H5(style={"font-weight": "600"}, id="date", children="Saturday, October 7, 2023"),
            html.H1(style={"font-size": "48pt"}, id="time", children="12:12PM")
        ]),
        html.Div(className="container", id="profileDiv4", children=[
            html.H5(style={"font-style": "italic"}, children="Preferences"),
            html.Div(id="preferencesForm", children=[
                html.Label(htmlFor="", children=[
                    html.H5("Temperature")
                ]),
                html.Div(children=[
                    dcc.Input(type="text", maxLength="3", id="tempInput"),
                    '\N{DEGREE SIGN}' + "C"
                ]),

                html.Label(htmlFor="", children=[
                    html.H5("Humidity")
                ]),
                html.Div(children=[
                    dcc.Input(type="text", maxLength="3", id="humidityInput"),
                    "%"
                ]),

                html.Label(htmlFor="", children=[
                    html.H5("Light Intensity")
                ]),
                html.Div(children=[
                    dcc.Input(type="text", maxLength="3", id="lightIntensityInput")
                ]),
            ])
        ]),
        html.Div(className="container", id="profileDiv5", children=[
            html.Button(id="saveProfileBtn", n_clicks=0, children="Save Profile")
        ]),
    ]),
    # Temperature section
    html.Div(className="container", id="tempHumFan", children=[
        html.Div(className="container", id="tempContainer", children=[
            html.Div(className="container", id="thermometerGauge"),
            html.H2("Current Temperature"),
            daq.Gauge(
                id='temp',
                className='gauge',
                color=theme['primary'],
                scale={'start': 0, 'interval': 5, 'labelInterval': 2},
                value=0,
                min=0,
                max=40,
            ),
            html.H3(id="temperatureHeading")
        ]),
        html.Div(className="container", id="humidity", children=[
            html.Div(className="container", id="humidityGauge"),
            html.H2("Current Humidity", style={"color": "#76c8e3"}),
            daq.Gauge(
                id='humidity_data',
                className='gauge',
                color=theme['primary'],
                scale={'start': 0, 'interval': 5, 'labelInterval': 2},
                value=0,
                min=0,
                max=100,
            ),
            html.H3(id="humidityHeading")
        ]),
        html.Div(className="container", id="fan", children=[
            html.P("fanOff", hidden=True, id="fan_state"),
            html.Img(src=app.get_asset_url("images/spinningFan.png"), id="fan-img", width="250", height="250"),
            html.Button("Turn On", id="fan-control-button", n_clicks=0)
        ]),
        html.Div(id="email-alert-container", children=[
            dbc.Alert(
                id="email-alert",
                is_open=False,
                duration=5000,
        )]),
    ]),

    # Light section
    html.Div(className="container", id="light", children=[
        html.Img(src="assets/images/phase1Off.png", id="lightImg"),
        html.Div(id="lightText", children=[
            html.H2("Current Light Intensity"),
            html.H2(id="lightNum", style={"color": "#FFCA10"}),
        ])
    ]),

    # Devices section
    html.Div(className="container", id="devices", children=[
        html.Img(src="assets/images/phone.png", id="devicesImg"),
        html.Div(id="devicesText", children=[
            html.H2("Wireless Devices Nearby"),
            html.H2(id='bluetoothDeviceCount')
        ])
    ]),
    html.Div(id="email-status"),
])
# Add a function to detect nearby Bluetooth devices
def detect_bluetooth_devices():
    global bluetooth_device_count
    while True:
        try:
            nearby_devices = bluetooth.discover_devices()
            bluetooth_device_count = len(nearby_devices)
        except Exception as e:
            print(f"Error discovering devices: {e}")
            bluetooth_device_count = 0

"""
Updates:
Temperature Gauge
Temperature Value Heading
Humidity Gauge
Humidity Value Heading
Light Value Heading
Light On/Off Image

If Temp value is over user's threshold
    Send email
If Light value is under user's threshold
    Turn light image on
Else
    Turn light image off
"""
@app.callback(
    Output("fan_state", "children", allow_duplicate=True),
    Output("temp", "value"),
    Output("temperatureHeading", "children"),
    Output("humidity_data", "value"),
    Output("humidityHeading", "children"),
    Output("lightNum", "children"),
    Output("lightImg", "src"),
    Output("loaded-user-profile", "data", allow_duplicate=True),
    Output("email-alert-container", "children", allow_duplicate=True),
    Output("date", "children"),
    Output("time", "children"),
    Output("bluetoothDeviceCount", "children"),
    Input("dht_light_thread_interval", "n_intervals"),
    State("loaded-user-profile", "data"),
    State("lightImg", "src"),
    prevent_initial_call=True
)
def dht_light_thread_update_page(n_intervals, loaded_user_profile, lightImgSrc):
    global dht_temp
    global dht_humidity
    global mqtt_light
    global can_send_email
    global waiting_on_response
    global fan_state
    global bluetooth_device_count
    global rfid_id
    global can_send_light_email
    global tempThreshold
    global user_email
    global temp_email_alert
    global months
    global send_signed_in_email

    alert = no_update
    if (temp_email_alert):
        alert = dbc.Alert(
        [
            html.H4("Email Sent to User", className="alert-heading"),
            html.P("An email has been sent to the user to turn on the fan for the temperature"),
        ],
        id="email-alert",
        is_open=True,
        duration=10000
        )
        temp_email_alert = False

    imgsrc = no_update
    if (loaded_user_profile is not None):
        tempThreshold = loaded_user_profile['tempThreshold']
        user_email = loaded_user_profile['email']
        if (float(dht_temp) > float(loaded_user_profile['tempThreshold']) and can_send_email and not waiting_on_response and fan_state == "fanOff"):
            can_send_email = False

        if (int(mqtt_light) < int(loaded_user_profile['lightIntensityThreshold']) and lightImgSrc == "assets/images/phase1Off.png"):
            GPIO.output(led_pin, GPIO.HIGH)
            imgsrc = "assets/images/phase1On.png"
            can_send_light_email = True
        if (int(mqtt_light) > int(loaded_user_profile['lightIntensityThreshold']) and lightImgSrc == "assets/images/phase1On.png"):
            GPIO.output(led_pin, GPIO.LOW)
            imgsrc = "assets/images/phase1Off.png"
    if (rfid_id is not None and (loaded_user_profile is None or rfid_id != loaded_user_profile['rfidTag'])):
        can_send_email = True
        waiting_on_response = False
        send_signed_in_email = True
        loaded_user_profile = get_user_profile(rfid_id)
    else:
        loaded_user_profile = no_update

    current_time = datetime.now()
    dateFinal = current_time.strftime("%A, %B %-d, %Y")
    timeFinal = current_time.strftime("%-I:%M%p")
    # dateFinal = months[current_time.month - 1] + ", " + str(current_time.day) + ", " + str(current_time.year)
    # timeFinal = str(current_time.hour) + " : " + str(current_time.minute)
    return fan_state, dht_temp, dht_temp, dht_humidity, dht_humidity, mqtt_light, imgsrc, loaded_user_profile, alert, dateFinal, timeFinal, str(bluetooth_device_count)

"""
When "Get user profile" button is clicked, get user's profile from database and store it in dcc.store
"""
# @app.callback(
#     Output("loaded-user-profile", "data"),
#     Input("get-user-profile-button", "n_clicks"),
#     prevent_initial_call=True
# )
def get_user_profile(rfid_id):
    con = sqlite3.connect("profiles_db.db")
    cur = con.cursor()
    res = cur.execute("SELECT * FROM Profile WHERE RfidTag = '" + rfid_id + "'")
    profile = res.fetchone()
    print(profile)
    if (profile is not None):
        return {'userID': profile[0], 'name': profile[1], 'tempThreshold': profile[2], 'humidityThreshold': profile[3], 'lightIntensityThreshold': profile[4], 'profilePic': profile[5], 'rfidTag': profile[6], 'email': profile[7]}
    cur.execute("INSERT INTO Profile(Name, TempThreshold, HumidityThreshold, LightIntensityThreshold, ProfilePic, RfidTag, Email) VALUES('<Insert Name Here>', 25, 50, 500, 'https://static.vecteezy.com/system/resources/previews/020/765/399/non_2x/default-profile-account-unknown-icon-black-silhouette-free-vector.jpg', '" + rfid_id + "', 'youremail@example.com')")
    con.commit()
    print("inserted")
    return get_user_profile(rfid_id)
    
    
"""
When "Save Profile" button is clicked, call update_database() and update dcc.store
"""
@app.callback(
    Output("loaded-user-profile", "data", allow_duplicate = True),  # Use a store to store preferences
    Output("email-alert-container", "children", allow_duplicate=True),
    Input("saveProfileBtn", "n_clicks"),
    State("loaded-user-profile", "data"),  # Use a store to store preferences
    State("nameInput", "value"),
    State("tempInput", "value"),
    State("humidityInput", "value"),
    State("lightIntensityInput", "value"),
    State("emailInput", "value"),
    prevent_initial_call=True
)
def save_preferences(n_clicks, loaded_user_profile, name_value, temp_value, humidity_value, light_intensity_value, email_value):
    global waiting_on_response
    global send_signed_in_email
    if (loaded_user_profile is not None):
        try:
            temp_value = int(temp_value)
            humidity_value = int(humidity_value)
            light_intensity_value = int(light_intensity_value)
            email_validate_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
            is_email_valid = re.fullmatch(email_validate_pattern, email_value)
            if (not is_email_valid):
                raise TypeError("invalid email")
            if (email_value != loaded_user_profile['email']):
                send_signed_in_email = True
            if (loaded_user_profile['email'] != email_value):
                waiting_on_response = False
        except:
            alert = dbc.Alert(
            [
                html.H4("Could not save profile", className="alert-heading"),
                html.P("One or more invalid fields"),
            ],
            id="email-alert",
            is_open=True,
            duration=5000
            )
            temp_email_alert = False
            return no_update, alert
        updated_user_profile = {'userID': loaded_user_profile['userID'], 'name': name_value, 'tempThreshold': temp_value, 'humidityThreshold': humidity_value, 'lightIntensityThreshold': light_intensity_value, 'profilePic': loaded_user_profile['profilePic'], 'rfidTag': loaded_user_profile['rfidTag'], 'email': email_value}
        update_database(updated_user_profile)
        alert = dbc.Alert(
        [
            html.H4("Profile Successfully Updated", className="alert-heading"),
        ],
        id="email-alert",
        is_open=True,
        duration=5000
        )
        temp_email_alert = False
        return updated_user_profile, alert
    else:
        alert = dbc.Alert(
        [
            html.H4("Couldn't Save Profile", className="alert-heading"),
            html.P("There is no loaded profile to save to"),
        ],
        id="email-alert",
        is_open=True,
        duration=5000
        )
        temp_email_alert = False
        return no_update, alert

"""
Update current user's profile in database
"""
def update_database(updated_user_profile):
    con = sqlite3.connect("profiles_db.db")
    cur = con.cursor()
    cur.execute("UPDATE Profile SET name=?, TempThreshold=?, HumidityThreshold=?, LightIntensityThreshold=?, ProfilePic=?, Email=? WHERE UserID=?",
                (updated_user_profile['name'], updated_user_profile['tempThreshold'], updated_user_profile['humidityThreshold'], updated_user_profile['lightIntensityThreshold'], updated_user_profile['profilePic'], updated_user_profile['email'], updated_user_profile['userID']))
    con.commit()
    con.close()
    return  # Reset the button click count

"""
When dcc.store is updated, load all the profile values into all the fields
"""
@app.callback(
    Output("nameInput", "value"),
    Output("tempInput", "value"),
    Output("humidityInput", "value"),
    Output("lightIntensityInput", "value"),
    Output("profilepic", "src"),
    Output("emailInput", "value"),
    Input("loaded-user-profile", "data"),  # Use a store to store preferences
    prevent_initial_call=True
)
def load_user_profile(loaded_user_profile):
    if loaded_user_profile is None:
        return no_update, no_update, no_update, no_update, no_update, no_update
    return loaded_user_profile['name'], loaded_user_profile['tempThreshold'], loaded_user_profile['humidityThreshold'], loaded_user_profile['lightIntensityThreshold'] , loaded_user_profile['profilePic'], loaded_user_profile['email']
"""
When the "Fan control" button is clicked, toggle "Fan state" hidden p
"""
@app.callback(
    Output("fan_state", "children"),
    Input("fan-control-button", "n_clicks"),
    prevent_initial_call=True
)
def toggle_fanState(n_clicks):
    global fan_state
    if fan_state == "fanOff":
        fan_state = "fanOn"
        return "fanOn"
    elif fan_state == "fanOn":
        fan_state = "fanOff"
        return "fanOff"

"""
When "Fan state" hidden p is updated, set fan image and fan button to the new state by calling the functions below
"""
@app.callback(
    Output("fan-img", "src"),
    Output("fan-control-button", "children"),
    Input("fan_state", "children"),
    prevent_initial_call=True
)
def update_fan(fan_state):
    if fan_state == "fanOff":
        return turnFanOff()
    elif fan_state == "fanOn":
        return turnFanOn()
def turnFanOn():
    GPIO.output(motor_pins[0],GPIO.HIGH)
    GPIO.output(motor_pins[1],GPIO.LOW)
    GPIO.output(motor_pins[2],GPIO.HIGH)
    return app.get_asset_url('images/spinningFan.gif'), "Turn Off"
def turnFanOff():
    GPIO.output(motor_pins[0],GPIO.LOW)
    GPIO.output(motor_pins[1],GPIO.LOW)
    GPIO.output(motor_pins[2],GPIO.LOW)
    return app.get_asset_url('images/spinningFan.png'), "Turn On"

"""
When "Send email" button is clicked, send an email asking to turn the fan on
"""
# @app.callback(
#     Output("email-status", "children"),
#     Output("email-alert-container", "children"),
#     Input("send-email-button", "n_clicks"),
#     prevent_initial_call=True
# )
def send_test_email(temp):
    global tempThreshold
    # Manually send a test email
    subject = "Temperature warning!"
    body = f"The temperature is: {temp} which is greater than {tempThreshold}\n If you wish to turn the fan on reply 'yes' in all caps"
    send_email(subject, body)
    alert = dbc.Alert(
        [
            html.H4("Email Sent to User", className="alert-heading"),
            html.P("An email has been sent to the user to turn on the fan for the temperature"),
        ],
        id="email-alert",
        is_open=True,
        duration=10000
    )
    return "Test email sent.", alert

# Callback to close the alert after 5 seconds
@app.callback(
    Output("email-alert", "is_open"),
    Input("email-status", "children"),
    Input("email-alert", "id")
)
def close_alert(status, alert_id):
    time.sleep(5)  # Wait for 5 seconds
    return False
"""
Connect to smtp server and send email
"""
def send_email(subject, body):
    global user_email
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(sender_email, user_email, message)
        print("Email sent successfully.")
    except Exception as e:
        print("Email could not be sent. Error:", str(e))

"""
Check for unread emails.
If there is an unread email
    Set 'can_send_email' to True
    If first word in email is 'YES'
        Return 'fanOn'
"""
def check_email_for_user_response():
    global can_send_email
    global waiting_on_response
    global fan_state
    global user_email
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(sender_email, password)
        mail.select("inbox")
        status, email_ids = mail.search(None, "UNSEEN")

        email_ids = email_ids[0].split()

        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            subject, encoding = decode_header(msg["Subject"])[0]

            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            print("From:", msg["From"])
            print("Subject:", subject)
            print("Date:", msg["Date"])

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        email_body = part.get_payload(decode=True).decode("utf-8")
                        print("Email Body:", email_body)

                        first_word = email_body.strip().split()[0]

                        if user_email not in msg["From"]:
                            return

                        waiting_on_response = False
                        if first_word.upper() == "YES":
                            print("Received 'YES' response. Turning on the fan...")
                            fan_state = "fanOn"
                            return "fanOn"
                        else:
                            fan_state = "fanOff"
                            print("No 'YES' found in the email body.")
        mail.logout()
    except Exception as e:
        print("Email retrieval error:", str(e))

@app.callback(
    Output("modal", "is_open"),
    Output("pfp_src_input", "value"),
    Output("loaded-user-profile", "data", allow_duplicate = True),
    Output("email-alert-container", "children", allow_duplicate=True),
    Input("profilepicedit", "n_clicks"),
    Input("savePfpBtn", "n_clicks"),
    Input("closePopupBtn", "n_clicks"),
    State("loaded-user-profile", "data"),
    State("pfp_src_input", "value"),
    State("modal", "is_open"),
    prevent_initial_call=True
)
def clicked_profile_pic(n_clicks1, n_clicks2, n_clicks3, loaded_user_profile, pfp_src_input, is_open):
    if (loaded_user_profile is None):
        alert = dbc.Alert(
        [
            html.H4("Can't Update Profile Picture", className="alert-heading"),
            html.P("There is no loaded profile to save to"),
        ],
        id="email-alert",
        is_open=True,
        duration=10000
        )
        temp_email_alert = False
        return False, no_update, no_update, alert

    if (is_open):
        if ctx.triggered_id == "closePopupBtn":
            return False, no_update, no_update, no_update
        if ctx.triggered_id == "savePfpBtn":
            loaded_user_profile['profilePic'] = pfp_src_input
            update_database(loaded_user_profile)
            return False, no_update, loaded_user_profile, no_update
    else:
        return True, loaded_user_profile['profilePic'], no_update, no_update
    
    # if ctx.triggered_id == "profilepicedit":
    #     return True, loaded_user_profile['profilePic'], no_update
    # if ctx.triggered_id == "closePopupBtn":
    #     return False, no_update, no_update
    # if ctx.triggered_id == "savePfpBtn":
    #     loaded_user_profile['profilePic'] = pfp_src_input
    #     update_database(loaded_user_profile)
    #     return False, no_update, loaded_user_profile

    # return False, no_update, no_update


"""
Code to loop for dht_thread
Reads temperature and humidity data from DHT and sets it to global variable
"""
def dht_loop():
    global dht_temp
    global dht_humidity

    dht = DHT.DHT(18)
    while True:
        for i in range(0,15):
            chk = dht.readDHT11()
            if (chk is dht.DHTLIB_OK):
                break
            sleep(0.1)
        dht_temp, dht_humidity = dht.temperature, dht.humidity

"""
Code to loop for mqtt_thread
Reads light data from MQTT server and sets it to global variable
"""
def mqtt_loop():
    """
    Python MQTT Subscription client - No Username/Password
    Thomas Varnish (https://github.com/tvarnish), (https://www.instructables.com/member/Tango172)
    Written for my Instructable - "How to use MQTT with the Raspberry Pi and ESP8266"
    """
    import paho.mqtt.client as mqtt

    global mqtt_light
    global connected

    def on_message(client, userdata, message):
        global mqtt_light
        mqtt_light = int(message.payload.decode("utf-8"))
        
    def on_message_rfid(client, userdata, message):
        global rfid_id
        rfid_id = message.payload.decode("utf-8")
        print(rfid_id)

    port = 1883
    mqtt_topic = "LightData"
    mqtt_topic_rfid = "RfidData"
    mqtt_broker_ip = "192.168.42.113"
    client = mqtt.Client("Light Reader")
    client.on_message = on_message
    client.connect(mqtt_broker_ip, port=port)
    client.subscribe(mqtt_topic)
    
    rfidClient = mqtt.Client("Rfid Reader")
    rfidClient.on_message = on_message_rfid
    rfidClient.connect(mqtt_broker_ip, port=port)
    rfidClient.subscribe(mqtt_topic_rfid)
    while True:
        client.loop_start()
        client.loop_stop()
        rfidClient.loop_start()
        rfidClient.loop_stop()
        
def CheckRfid():
    while True:
        global rfid_id
        rfid = RFID.RFID()
        
        condition = isinstance(rfid_id, int)
        if condition:
            break
        elif profileChangeSwitch:
            profileChangeSwitch = False
            break
    print("Condition met. Stopping function.")
    
def CancelButton():
    profileChangeSwitch = True

def email_loop():
    global can_send_email
    global waiting_on_response
    global dht_temp
    global can_send_light_email
    global temp_email_alert
    global send_signed_in_email

    while True:
        if (can_send_light_email):
            # Get current time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Send notification email
            subject = "LED Turned On"
            body = f"The LED was turned on at {current_time}"
            send_email(subject, body)
            can_send_light_email = False
            sleep(2)
        if (can_send_email != True and waiting_on_response != True):
            send_test_email(dht_temp)
            temp_email_alert = True
            can_send_email = True
            waiting_on_response = True
        if (can_send_email and waiting_on_response):
            check_email_for_user_response()
            sleep(2)
        if (send_signed_in_email):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subject = "Signed in to Dashboard"
            body = f"You just signed to the Dashboard at {current_time}"
            send_email(subject, body)
            send_signed_in_email = False
            sleep(2)


if __name__ == '__main__':
    dht_thread = threading.Thread(target=dht_loop)
    dht_thread.start()

    mqtt_thread = threading.Thread(target=mqtt_loop)
    mqtt_thread.start()

    email_thread = threading.Thread(target=email_loop)
    email_thread.start()
    # Start the Bluetooth discovery process in a separate thread
    bluetooth_thread = threading.Thread(target=detect_bluetooth_devices)
    bluetooth_thread.start()

    app.run(debug=True)
