import argparse


from bots_platform import ui, PlatformGui, ExchangeModel


PROGRAM = 'Trading Bots Platform'
VERSION = 'v1'
TARGET = 'bybit'
TITLE = f'{PROGRAM} {VERSION} [{TARGET}]'
DESCRIPTION = f"""
{TITLE} - a software tool that allows users to test and apply automated trading strategies in the crypto market.
""".strip()


def main(host, port):
    global TITLE
    print("Starting...")
    ui.add_head_html('''
        <style type="text/tailwindcss">
            body {
                font-size: 100%;
            }
            .nicegui-link, a {
                color: #fff;
            }
            .q-table th, .q-table td {
                font-size: 100%;
            }
        </style>
    ''')
    ui.colors(primary='#777')
    platform_gui = PlatformGui(TITLE)
    exchange_model = ExchangeModel()
    platform_gui.set_exchange_model(exchange_model)
    platform_gui.init()
    ui.run(host=host, port=port, title=TITLE, dark=True, language='en-US',
           reload=False, endpoint_documentation='none',
           show_welcome_message=False)


if __name__ in {"__main__", "__mp_main__"}:
    parser = argparse.ArgumentParser(prog='./main', description=DESCRIPTION)
    parser.add_argument('--host', default=None, help='hostname')
    parser.add_argument('--port', default=None, help='port')
    args = parser.parse_args()
    main(args.host, args.port)
