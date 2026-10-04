import React from "react";
import { Bell, Check } from "lucide-react";

export default function Notifications({ notifications, setNotifications }) {
  const markAll = () => setNotifications(n => n.map(x => ({ ...x, read: true })));
  return (
    <>
      <section className="pageHead">
        <div>
          <span className="eyebrow"></span>
          <h1></h1>
          <p></p>
        </div>
        <button className="btn ghost" onClick={markAll}><Check size={16} />&nbsp;</button>
      </section>
      <section className="pageBody">
        <div className="panel list">
          {notifications.map(n => (
            <div className={"notification" + (!n.read ? " unread" : "")} key={n.id}>
              <Bell size={19} />
              <div>
                <strong>{n.title}</strong>
                <p>{n.body}</p>
                <small>{n.time}</small>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
