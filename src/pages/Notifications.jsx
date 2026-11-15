
import React, {
  useCallback,
  useEffect,
  useRef,
  useState
} from 'react';

import {
  Bell,
  Check,
  RefreshCw,
  AlertCircle
} from 'lucide-react';

import { api } from '../api';

// Convert notification timestamps to readable time
function ago(ts) {
  const s = Math.max(0, Date.now() / 1000 - ts);

  if (s < 60) return 'Just now';
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} hours ago`;
  if (s < 172800) return 'Yesterday';

  return new Date(ts * 1000).toLocaleDateString();
}

export default function Notifications({
  onError,
  onChanged
}) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState('');
  const [retryAction, setRetryAction] = useState(null);

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [busyId, setBusyId] = useState(null);

  const mounted = useRef(false);
  const requestId = useRef(0);

  // Handle errors and expired login sessions
  const fail = useCallback(
    (e, action = null) => {
      const message =
        e?.message || 'Something went wrong. Please try again.';

      setError(message);
      setRetryAction(() => action);

      if (e?.status === 401) {
        onError?.(e);
      }
    },
    [onError]
  );

  // Load notifications from backend
  const load = useCallback(async () => {
    const currentRequest = ++requestId.current;

    setLoading(true);
    setError('');
    setRetryAction(null);

    try {
      const data = await api('/me/notifications');

      if (
        mounted.current &&
        currentRequest === requestId.current
      ) {
        setItems(Array.isArray(data) ? data : []);
      }

      return true;
    } catch (e) {
      if (
        mounted.current &&
        currentRequest === requestId.current
      ) {
        fail(e, load);
      }

      return false;
    } finally {
      if (
        mounted.current &&
        currentRequest === requestId.current
      ) {
        setLoading(false);
      }
    }
  }, [fail]);

  // Initial notification loading
  useEffect(() => {
    mounted.current = true;

    load();

    return () => {
      mounted.current = false;
      requestId.current += 1;
    };
  }, [load]);

  // Mark all notifications as read
  const markAll = async () => {
    if (busy || busyId !== null || loading) return;

    setBusy(true);
    setError('');
    setRetryAction(null);

    try {
      await api('/me/notifications/read', {
        method: 'POST'
      });

      if (mounted.current) {
        setItems(previous =>
          previous
            ? previous.map(n => ({
                ...n,
                read: true
              }))
            : previous
        );

        onChanged?.();
      }
    } catch (e) {
      if (mounted.current) {
        fail(e, markAll);
      }
    } finally {
      if (mounted.current) {
        setBusy(false);
      }
    }
  };

  // Mark one notification as read
  const markOne = async notification => {
    if (
      notification.read ||
      busy ||
      busyId !== null ||
      loading
    ) {
      return;
    }

    setBusyId(notification.id);
    setError('');
    setRetryAction(null);

    try {
      await api(
        `/me/notifications/${notification.id}/read`,
        { method: 'PUT' }
      );

      if (mounted.current) {
        setItems(previous =>
          previous
            ? previous.map(n =>
                n.id === notification.id
                  ? { ...n, read: true }
                  : n
              )
            : previous
        );

        onChanged?.();
      }
    } catch (e) {
      if (mounted.current) {
        fail(e, () => markOne(notification));
      }
    } finally {
      if (mounted.current) {
        setBusyId(null);
      }
    }
  };

  const unread = items
    ? items.filter(n => !n.read).length
    : 0;

  const retry = () => {
    if (retryAction) {
      retryAction();
    } else {
      load();
    }
  };

  return (
    <>
      {/* PAGE HEADER */}
      <section className="pageHead">
        <div>
          <span className="eyebrow">
            CIVIC ISSUE MATCHMAKER
          </span>

          <h1>Notifications</h1>

          <p>
            New matches, task events,
            and account updates.
          </p>
        </div>

        <div
          style={{
            display: 'flex',
            gap: 10,
            flexWrap: 'wrap'
          }}
        >
          <button
            type="button"
            className="btn ghost"
            onClick={load}
            disabled={loading || busy || busyId !== null}
          >
            <RefreshCw size={16} />
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>

          <button
            type="button"
            className="btn ghost"
            disabled={
              !unread ||
              loading ||
              busy ||
              busyId !== null
            }
            onClick={markAll}
          >
            <Check size={16} />
            {busy ? 'Updating...' : 'Mark all read'}
          </button>
        </div>
      </section>

      {/* PAGE CONTENT */}
      <section className="pageBody">

        {/* ERROR MESSAGE */}
        {error && (
          <div
            className="msg error"
            role="alert"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              flexWrap: 'wrap',
              padding: 14,
              marginBottom: 16
            }}
          >
            <AlertCircle size={20} />

            <span style={{ flex: 1 }}>
              {error}
            </span>

            {retryAction && (
              <button
                type="button"
                className="btn"
                onClick={retry}
                disabled={
                  loading ||
                  busy ||
                  busyId !== null
                }
              >
                <RefreshCw size={16} />
                Retry
              </button>
            )}

            <button
              type="button"
              className="textButton"
              onClick={() => {
                setError('');
                setRetryAction(null);
              }}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* LOADING STATE */}
        {loading && !items && (
          <div
            className="panel"
            role="status"
            style={{ padding: 24 }}
          >
            Loading notifications...
          </div>
        )}

        {/* FAILED INITIAL LOAD */}
        {!loading && !items && (
          <div
            className="panel"
            style={{ padding: 24 }}
          >
            <h3>Unable to load notifications</h3>

            <p>
              The notification service is unavailable.
              Please check your connection and try again.
            </p>

            <button
              type="button"
              className="btn primary"
              onClick={load}
            >
              <RefreshCw size={16} />
              Try Again
            </button>
          </div>
        )}

        {/* EMPTY STATE */}
        {!loading &&
          items &&
          items.length === 0 && (
            <div
              className="panel"
              style={{ padding: 24 }}
            >
              <Bell size={28} />

              <h3>No notifications yet</h3>

              <p>
                New issue matches, messages,
                and account updates will appear here.
              </p>

              <button
                type="button"
                className="btn"
                onClick={load}
              >
                <RefreshCw size={16} />
                Refresh Notifications
              </button>
            </div>
          )}

        {/* NOTIFICATION LIST */}
        {items && items.length > 0 && (
          <div className="panel list">
            {items.map(notification => (
              <button
                type="button"
                key={notification.id}
                className={
                  'notification' +
                  (notification.read ? '' : ' unread')
                }
                onClick={() => markOne(notification)}
                disabled={
                  loading ||
                  busy ||
                  busyId !== null
                }
              >
                <Bell size={19} />

                <div>
                  <strong>
                    {notification.title}
                  </strong>

                  <p>{notification.body}</p>

                  <small>
                    {ago(notification.created_at)}
                    {busyId === notification.id &&
                      ' | Updating...'}
                  </small>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
