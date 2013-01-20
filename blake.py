from proxyherd import proxylaunch

if __name__ == '__main__':
    proxylaunch.initialize('Blake', 12460, '127.0.0.1', 12465, [12466, 12467])
