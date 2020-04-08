#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
import time


class ServerProtocol(asyncio.Protocol):
    login: str = None
    list_of_messages: list = []
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        list_of_clients = []
        print(data)
        decoded = data.decode()

        if self.login is not None:
            # ЗАДАНИЕ 1 в ходе выполнения первого задания для отладки я выводил список всех пользователей,
            # оставлю это как доп. фичу
            if decoded.startswith("user_list"):
                for user in self.server.clients:
                    self.transport.write(f"Пользователь:{user.login}\n".encode())
            else:
                self.send_message(decoded)

        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                print(self.login)
                # ЗАДАНИЕ 1 я хотел обращаться в следующем if напрямую к self.server.clients, но это не список, а объект
                # поэтому пришлось ввести дополнительный промежуточный список list_of_clients
                for user in self.server.clients:
                    list_of_clients.append(user.login)
                # ЗАДАНИЕ 1 Просто проверем наличие текущего логина в списке всех пользователей, если он есть,
                # то просто дропаем соединение, предварительно уснув, чтоб сообщение было видно в консоли putty
                if self.login in list_of_clients[:-1]:
                    self.transport.write(f"Логин {self.login} занят, попробуйте другой. \n".encode())
                    time.sleep(2)
                    self.transport.close()
                else:
                    self.transport.write(
                        f"Привет, {self.login}!\n Для просмотра списка пользователей, введите 'user_list'. \n".encode()
                    )
                    self.transport.write(f"Последние 10 сообщений \n".encode())
                    # ЗАДАНИЕ 2 Вызываем новый метод при добавлении нового пользователя
                    self.send_history(self.list_of_messages)
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    # ЗАДАНИЕ 2 С каждой отпрвой сообщения мы складируем их в список-аттрибут класса
    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.list_of_messages.append(message)
        for user in self.server.clients:
            user.transport.write(message.encode())

    # ЗАДАНИЕ 2 Выводим последние 10 сообщений
    def send_history(self, content: list):
        for message in content[-10:]:
            self.transport.write(message.encode())


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
