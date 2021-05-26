from socket import socket, AF_INET, SOCK_STREAM
import _thread
import json
import pandas as pd
import time
import datetime
import matplotlib.pyplot as plt

HOST = "0.0.0.0"
PORT = 42069
BUFF = 256

RUN = True

FILE_NAME_FORMAT = "ispindel_data_{}.csv"

server_sock = socket(AF_INET, SOCK_STREAM)
server_sock.bind((HOST, PORT))
server_sock.listen(5)


def handler(client_sock, addr):
    seconds_since_e = int(time.time())
    print(str(datetime.datetime.fromtimestamp(seconds_since_e)))

    S = ""
    while True:
        data = client_sock.recv(BUFF)
        if not data:
            break
        msg = data.decode("utf-8")
        S += msg

    ispindel_data = json.loads(S)
    ispindel_data["date"] = seconds_since_e
    file_name = FILE_NAME_FORMAT.format(ispindel_data["name"])

    print("\t", ispindel_data["name"], addr)
    print("\tT°: {}\n\tGravity: {}\n\tAngle: {}\n\tBattery: {}" \
          .format(*[ispindel_data[i] for i in ["temperature",
                                               "gravity",
                                               "angle",
                                               "battery"]]))

    try:
        df_ispindel_data = pd.read_csv(file_name, index_col=0)
    except FileNotFoundError:
        df_ispindel_data = pd.DataFrame()
    df_ispindel_data = df_ispindel_data.append(ispindel_data, ignore_index=True)
    df_ispindel_data.to_csv(file_name)
    print("\tSaved")

    client_sock.close()


def server_thread(server_sock):
    print("Server started")
    while RUN:
        try:
            client_sock, addr = server_sock.accept()
        except OSError:
            break
        print("###Connected from: " + str(addr))
        _thread.start_new_thread(handler, (client_sock, addr))
    print("Server loop broken")


def double_plot(ax, x, y, z, y_label, z_label):
    color = 'tab:red'
    ax.set_xlabel('Days')
    ax.set_ylabel(y_label, color=color)
    ax.plot(x, y, "-o", color=color)
    ax.tick_params(axis='y', labelcolor=color)

    ax2 = ax.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel(z_label, color=color)  # we already handled the x-label with ax1
    ax2.plot(x, z, "-o", color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    ax.minorticks_on()
    ax.grid(b=True, which='major', color='k', linestyle='-')
    ax.grid(b=True, which='minor', color=(0.25, 0.25, 0.25), linestyle=':')


def plot_csv(name):
    file_name = FILE_NAME_FORMAT.format(name)
    try:
        df_ispindel_data = pd.read_csv(file_name, index_col=0)
    except FileNotFoundError:
        print("File for ispindel {} does not exist".format(name))
        return None

    try:
        t = df_ispindel_data["date"].to_numpy()
        t = (t - t[0]) / 3600 / 24
        gravity = df_ispindel_data["gravity"].to_list()
        temperature = df_ispindel_data["temperature"].to_list()
        angle = df_ispindel_data["angle"].to_list()
        battery = df_ispindel_data["battery"].to_list()
    except KeyError:
        print("Something went wrong when reading CSV. One or more column are missing")
        return None

    ax1 = plt.subplot(211)
    double_plot(ax1, t, temperature, gravity, "Temperature (°C)", "Gravity (°P)")
    ax1.set_title(file_name)

    ax2 = plt.subplot(212)
    double_plot(ax2, t, angle, battery, "Angle (°)", "Battery (V)")

    plt.tight_layout()
    plt.show()


print("Running on:", (HOST, PORT))
_thread.start_new_thread(server_thread, (server_sock,))

time.sleep(2)
user_input = input(">>")
while user_input != "close":
    plot_csv(user_input)
    user_input = input(">>")
    if user_input == "close": break

RUN = False

server_sock.close()
print("Socket closed")
time.sleep(2)
