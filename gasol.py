from proxyherd import proxylaunch

if __name__ == '__main__':
    proxylaunch.initialize('Gasol', 12463, '127.0.0.1', 12468, [12466, 12467])
