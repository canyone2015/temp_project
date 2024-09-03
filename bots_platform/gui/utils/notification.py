from nicegui import ui


class Notification:
    def __init__(self, nicegui_notification_object):
        self._nicegui_notification_object = nicegui_notification_object

    def show(self):
        notification_id = self._nicegui_notification_object.id
        ui.run_javascript(f"""
            let data_id = "nicegui-dialog-{notification_id}";
            var el = document.querySelector('[data-id="' + data_id + '"]');
            el.style.display = '';
        """)

    def hide(self):
        notification_id = self._nicegui_notification_object.id
        ui.run_javascript(f"""
            let data_id = "nicegui-dialog-{notification_id}";
            var el = document.querySelector('[data-id="' + data_id + '"]');
            el.style.display = 'none';
        """)

    def get(self):
        return self._nicegui_notification_object
