from dash import Dash, dcc, html, Input, Output, State, no_update
import dash_daq as daq
import smtplib
import imaplib
import email
from email.header import decode_header
import threading
import Freenove_DHT as DHT
import RPi.GPIO as GPIO
from time import sleep
import sqlite3

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# List all pins for sensor (James)
sensor_pins = [18, 23, 24]
sensor_data = dict.fromkeys(["temperature", "humidity", "light"], None)
canSend = True

motor_pins = [22, 27, 17]
GPIO.setup(motor_pins[0],GPIO.OUT)
GPIO.setup(motor_pins[1],GPIO.OUT)
GPIO.setup(motor_pins[2],GPIO.OUT)

sender_email = "testvanier@gmail.com"
receiver_email = "hajimeadams289@gmail.com"
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
    dcc.Interval(id="readSensorsAndEmailInterval", interval=5000),
    dcc.Store(id='loaded-user-profile', storage_type='session'),
    # User preference section
    html.Div(className="container", id="profile", children=[
        html.Div(className="container", id="profileDiv1", children=[
            html.Img(src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAOEAAADhCAMAAAAJbSJIAAAAPFBMVEXk5ueutLepsLPo6uursbXJzc/p6+zj5ea2u76orrKvtbi0ubzZ3N3O0dPAxcfg4uPMz9HU19i8wcPDx8qKXtGiAAAFTElEQVR4nO2d3XqzIAyAhUD916L3f6+f1m7tVvtNINFg8x5tZ32fQAIoMcsEQRAEQRAEQRAEQRAEQRAEQRAEQRAEQRAEQRAEQTghAJD1jWtnXJPP/54IgNzZQulSmxvTH6oYXX4WS+ivhTbqBa1r26cvCdCu6i0YXbdZ0o4A1rzV+5IcE3YE+z58T45lqo7g1Aa/JY5tgoqQF3qb382x7lNzBLcxft+O17QUYfQI4IIeklKsPSN4i6LKj/7Zm8n99RbHJpEw9gEBXNBpKIYLJqKYRwjOikf//r+J8ZsVuacbqCMNleI9TqGLGqMzhnVdBOdd6F/RlrFijiCoVMk320CBIahUxTWI0KKEcJqKbMdpdJb5QvdHq6wCI5qhKlgGMS/RBHkubWDAE+QZxB4xhCyDiDkLZxgGEVdQldzSKbTIhmZkFkSEPcVvmBn2SMuZB9od7fQDsMiDdKJjFUSCQarM5WirZ3C2TT/htYnyPcPfgrFHWz0BI74gr6J/IZiGUxAZGQLqmvQLTrtE/Go4YxhVRIpEw+sww1IIcqr5NKmUUzLF3d4/qPkYIp2T/obPuemlojFUR4t9Q2Vojhb7BmgElWHzLPH8hucfpefPNFTVgs9h1AdU/Pin96vwWbWdf+X9Absn3OdO34aMdsDnP8WgKYisTqI6CkNGqZQo1XA6Ef6AU32SJzOcBukHPF07/xNSgmHKa5BOhtezv6mA/rYJpwXNAnbRZ1XuF3BzDcO3vpA3+ny2909gbqE4hhD3LIPhLLyBNhPZvbZ3B+3tPYa18A7auSlXQayKwTPNLKDcuOB0xPYKDPFTkWsevQPRZ1J8Hji9I1KQ34r7hZhrwNwOZ97QxNx0drwn4QI0wQk1DcEsfKCWKdxVvxPSNUIp/knmAXT+nT+Ko3+0H96rcNb3m1fx7MBTJdeBJ7uFcWsc0wvgAsC4pROW0l2inbAmIBv/7GZmuhQH6API2rr8T0e6yuZJ+80A9LZeG62T3tik31XwxtwZcizKuTHkMjB1WdZde4Kmic/A5ZI3rr1ae21d08PlVHYfAaxw9G9CYRbJ+8ZdbTcMRV1XM3VdF0M32vtoTdZ0+u29s0OttJ5bz64UwinjaFMVY9vkqc3KKSxN21Xl+0L4Q3Vuv1tYl0pqnX6ms4XetFz7gdZVAgUEoJntfOUe4ZwsHd9FzqQ3Vv6xe41l0XJcqcKl6TZvlv7ClAW3BsqQW4X7ypApB8dmTgK4IX5wvqIVj33HtD2qSG4BqznxdIefL27Y4sahi0MdIdvUsDva8agGGbCtITmCY31MHD2O0uIdh/0rJDQ1VX5Zdxz3rR2QDbv6qXl9vudzqQtGm1Jv9LDXOsfvvB7VcZ8PDKD0mQ1VHPYQ9O+Yj4hR1IUD8rBnn3ho2m8oQMxbCFiKlL2ioSW5heeJqegED52CzxCtcGD3Kv8Wms9EYLyUhwaFIhSMBClevWEmiK/Iaogu4H7sg6ppQhQG8RUqivuTGOAJOg6FfgW0q0M0PQMRMEgXaeNf3SYDZ8PIMI0+wHgr/MgN7wYwpiLjCCqM6ydUDZLQiB6nDdNC8SDyig3jPPpFXGcC9O8BUBDVmgBY59E7Md/35Loe/UVEECEJwYggJjELZ4J71SaQSBeC02n4Da29CayJNA28SAhd2CQyC1Xw6pSmGSINQVuMhAZp4DClan9MgmkDDNmezqwS8sgtlXK/EPBhoaSmYVC/F7IO1jQEdHOlabpKh3+jzLQSTUiq4X2I+Ip/zU8rlaqAvkS21ElR+gqu3zbjjL+hIAiCIAiCIAiCIAiCsCf/AKrfVhSbvA+DAAAAAElFTkSuQmCC", id="profilepic")
        ]),
        html.Div(className="container", id="profileDiv2", children=[
            html.H5(style={"font-style": "italic"}, children="Welcome"),
            dcc.Input(type="text", style={"font-size": "42pt", "font-weight": "bold"}, value="<Username>", id="nameInput")
        ]),
        html.Div(className="container", id="profileDiv3", children=[
            html.H5(style={"font-weight": "600"}, children="Saturday, October 7, 2023"),
            html.H1(style={"font-size": "48pt"}, children="12:12PM")
        ]),
        html.Div(className="container", id="profileDiv4", children=[
            html.H5(style={"font-style": "italic"}, children="Preferences"),
            html.Div(id="preferencesForm", children=[
                html.Label(htmlFor="", children=[
                    html.H5("Temperature")
                ]),
                html.Div(children=[
                    dcc.Input(type="text", maxLength="3", value="27", id="tempInput"),
                    '\N{DEGREE SIGN}' + "C"
                ]),

                html.Label(htmlFor="", children=[
                    html.H5("Humidity")
                ]),
                html.Div(children=[
                    dcc.Input(type="text", maxLength="3", value="70", id="humidityInput"),
                    "%"
                ]),

                html.Label(htmlFor="", children=[
                    html.H5("Light Intensity")
                ]),
                html.Div(children=[
                    dcc.Input(type="text", maxLength="3", value="505", id="lightIntensityInput")
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
        ])
    ]),

    # Light section
    html.Div(className="container", id="light", children=[
        html.Img(src="assets/images/phase1On.png", id="lightImg"),
        html.Div(id="lightText", children=[
            html.H2("Current Light Intensity"),
            html.H2("495", style={"color": "#FFCA10"})
        ])
    ]),

    # Devices section
    html.Div(className="container", id="devices", children=[
        html.Img(src="assets/images/phone.png", id="devicesImg"),
        html.Div(id="devicesText", children=[
            html.H2("Wireless Devices Nearby"),
            html.H2("7")
        ])
    ]),
    html.Button("Send Test Email", id="send-email-button"),
    html.Div(id="email-status"),
    html.Button("Get User Profile", id="get-user-profile-button"),
])

# Output("nameInput", "children"),
#     Output("tempInput", "value"),
#     Output("humidityInput", "value"),
#     Output("lightIntensityInput", "value"),
@app.callback(
    Output("loaded-user-profile", "data"),
    Input("get-user-profile-button", "n_clicks"),
    prevent_initial_call=True
)
def get_user_profile(n_clicks):
    con = sqlite3.connect("profiles_db.db")
    cur = con.cursor()
    res = cur.execute("SELECT * FROM Profile WHERE UserID = 1")
    profile = res.fetchone()
    return {'userID': profile[0], 'name': profile[1], 'tempThreshold': profile[2], 'humidityThreshold': profile[3], 'lightIntensityThreshold': profile[4], 'profilePic': profile[5]}
    #return profile[1], profile[2], profile[3], profile[4]

@app.callback(
    Output("fan_state", "children", allow_duplicate=True),
    Output("temp", "value"),
    Output("temperatureHeading", "children"),
    Output("humidity_data", "value"),
    Output("humidityHeading", "children"),
    Input("readSensorsAndEmailInterval", "n_intervals"),
    State("loaded-user-profile", "data"),
    prevent_initial_call=True
)
def sensor_and_email_reader(n_intervals, loaded_user_profile):
    global sensor_data
    global canSend
    
    print("Measurement counts: ", n_intervals)
    temperature, humidity = dhtReading(sensor_pins[0])
#loaded_user_profile['tempThreshold']
    if (temperature > 24 and canSend):
        send_test_email(temperature)
        canSend = False
    
    user_response = check_email_for_user_response()
    if user_response == "fanOn":
        return user_response, temperature, temperature, humidity, humidity
    return no_update, temperature, temperature, humidity, humidity

# callback for saving preferences
@app.callback(
    Output("loaded-user-profile", "data", allow_duplicate = True),  # Use a store to store preferences
    Input("saveProfileBtn", "n_clicks"),
    State("loaded-user-profile", "data"),  # Use a store to store preferences
    State("nameInput", "value"),
    State("tempInput", "value"),
    State("humidityInput", "value"),
    State("lightIntensityInput", "value"),
    prevent_initial_call=True
)

def save_preferences(n_clicks, loaded_user_profile, name_value, temp_value, humidity_value, light_intensity_value):
    updated_user_profile = {'userID': loaded_user_profile['userID'], 'name': name_value, 'tempThreshold': temp_value, 'humidityThreshold': humidity_value, 'lightIntensityThreshold': light_intensity_value, 'profilePic': loaded_user_profile['profilePic']}
    #user_preferences = {'temp': temp_value, 'humidity': humidity_value, 'light_intensity': light_intensity_value}
    update_database(updated_user_profile)
    return updated_user_profile

def update_database(updated_user_profile):
    con = sqlite3.connect("profiles_db.db")
    cur = con.cursor()
    cur.execute("UPDATE Profile SET name=?, TempThreshold=?, HumidityThreshold=?, LightIntensityThreshold=? WHERE UserID=?",
                (updated_user_profile['name'], updated_user_profile['tempThreshold'], updated_user_profile['humidityThreshold'], updated_user_profile['lightIntensityThreshold'], updated_user_profile['userID']))
    con.commit()
    con.close()
    return  # Reset the button click count

@app.callback(
    Output("nameInput", "value"),
    Output("tempInput", "value"),
    Output("humidityInput", "value"),
    Output("lightIntensityInput", "value"),
    Output("profilepic", "src"),
    Input("loaded-user-profile", "data"),  # Use a store to store preferences
    prevent_initial_call=True
)
def load_user_profile(loaded_user_profile):
    if loaded_user_profile is None:
        return no_update, no_update, no_update, no_update, no_update
    return loaded_user_profile['name'], loaded_user_profile['tempThreshold'], loaded_user_profile['humidityThreshold'], loaded_user_profile['lightIntensityThreshold'] , loaded_user_profile['profilePic'] 

@app.callback(
    Output("fan_state", "children"),
    Input("fan-control-button", "n_clicks"),
    State("fan_state", "children"),
    prevent_initial_call=True
)
def toggle_fanState(n_clicks, fan_state):
    if fan_state == "fanOff":

        return "fanOn"
    elif fan_state == "fanOn":
        return "fanOff"

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

#email sending and receiving logic:
@app.callback(
    Output("email-status", "children"),
    Input("send-email-button", "n_clicks"),
    prevent_initial_call=True
)

def send_test_email(temp):
    # Manually send a test email
    subject = "Temperature warning!"
    body = f"The temperature is: {temp} which is greater than 24\n If you wish to turn the fan on reply 'yes' in all caps"
    send_email(subject, body)
    return "Test email sent."

def send_email(subject, body):
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(sender_email, receiver_email, message)
        print("Email sent successfully.")
    except Exception as e:
        print("Email could not be sent. Error:", str(e))

def check_email_for_user_response():
    global canSend
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

                        if first_word.upper() == "YES":
                            print("Received 'YES' response. Turning on the fan...")
                            canSend = True
                            return "fanOn"
                        else:
                            canSend = True
                            print("No 'YES' found in the email body.")
        mail.logout()
    except Exception as e:
        print("Email retrieval error:", str(e))


#Sensor Functions: (James)

# (James)
            
#DHT (James)
def dhtReading(sensor_index):
    dht = DHT.DHT(sensor_index) #create a DHT class object

    for i in range(0,15):
        chk = dht.readDHT11() #read DHT11 and get a return value. Then determine whether
        #data read is normal according to the return value.
        if (chk is dht.DHTLIB_OK): #read DHT11 and get a return value. Then determine
        #whether data read is normal according to the return value.
            print("DHT11,OK!")
            break
        time.sleep(0.1)

    sensor_data['temperature'] = dht.temperature
    sensor_data['humidity'] = dht.humidity
    print("Humidity : %.2f, \t Temperature : %.2f \n"%(dht.humidity,dht.temperature))
    return dht.temperature, dht.humidity

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
