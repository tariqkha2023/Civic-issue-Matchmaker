
import React, {
  useCallback,
  useEffect,
  useRef,
  useState
} from 'react';

import { Send, RefreshCw, AlertCircle } from 'lucide-react';
import { api } from '../api';

// Generate initials for conversation avatars
const initials = (name = '') =>
  name
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map(word => word[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

export default function Messages({ onError, onChanged }) {
  const [people, setPeople] = useState(null);
  const [active, setActive] = useState(null);
  const [thread, setThread] = useState([]);

  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const [errorAction, setErrorAction] = useState(null);

  const [loading, setLoading] = useState(true);
  const [threadLoading, setThreadLoading] = useState(false);
  const [busy, setBusy] = useState(false);

  const end = useRef(null);
  const mounted = useRef(false);
  const requestId = useRef(0);

  // Handle API errors
  const fail = useCallback(
    (e, retryAction = null) => {
      const message =
        e?.message || 'Request failed. Please try again.';

      setError(message);
      setErrorAction(() => retryAction);

      if (e?.status === 401) {
        onError?.(e);
      }
    },
    [onError]
  );

  // Load available conversations
  const loadPeople = useCallback(async () => {
    setLoading(true);
    setError('');
    setErrorAction(null);

    try {
      const data = await api('/messages/conversations');

      if (mounted.current) {
        setPeople(Array.isArray(data) ? data : []);
      }

      return true;
    } catch (e) {
      if (mounted.current) {
        fail(e, loadPeople);
      }

      return false;
    } finally {
      if (mounted.current) {
        setLoading(false);
      }
    }
  }, [fail]);

  // Open a selected conversation
  const open = useCallback(
    async id => {
      const currentRequest = ++requestId.current;

      setThreadLoading(true);
      setError('');
      setErrorAction(null);

      try {
        const data = await api('/messages/' + id);

        if (
          !mounted.current ||
          currentRequest !== requestId.current
        ) {
          return false;
        }

        setActive(data.user);
        setThread(
          Array.isArray(data.messages) ? data.messages : []
        );

        onChanged?.();

        // Refresh conversation list without interrupting thread
        try {
          const updated = await api('/messages/conversations');

          if (
            mounted.current &&
            currentRequest === requestId.current
          ) {
            setPeople(Array.isArray(updated) ? updated : []);
          }
        } catch {
          // Thread loaded successfully; list refresh is optional
        }

        return true;
      } catch (e) {
        if (
          mounted.current &&
          currentRequest === requestId.current
        ) {
          fail(e, () => open(id));
        }

        return false;
      } finally {
        if (
          mounted.current &&
          currentRequest === requestId.current
        ) {
          setThreadLoading(false);
        }
      }
    },
    [fail, onChanged]
  );

  // Load conversations when page opens
  useEffect(() => {
    mounted.current = true;
    loadPeople();

    return () => {
      mounted.current = false;
      requestId.current += 1;
    };
  }, [loadPeople]);

  // Scroll to the newest message
  useEffect(() => {
    if (!threadLoading) {
      end.current?.scrollIntoView?.({
        block: 'end',
        behavior: 'smooth'
      });
    }
  }, [thread, threadLoading]);

  // Send a message
  const send = async e => {
    e?.preventDefault?.();

    if (!text.trim() || !active || busy) {
      return;
    }

    const message = text.trim();
    const recipientId = active.user_id;

    setBusy(true);
    setError('');
    setErrorAction(null);

    try {
      await api('/messages', {
        method: 'POST',
        body: {
          recipient_id: recipientId,
          body: message
        }
      });

      // Clear text only after successful delivery
      setText('');

      // Reload conversation after sending
      await open(recipientId);
    } catch (e) {
      // Preserve text if sending fails.
      // Do not automatically resend to avoid duplicates.
      fail(e, null);
    } finally {
      if (mounted.current) {
        setBusy(false);
      }
    }
  };

  const retry = () => {
    if (errorAction) {
      errorAction();
    } else {
      loadPeople();
    }
  };

  return (
    <>
      <section className="pageHead">
        <div>
          <span className="eyebrow">
            CIVIC ISSUE MATCHMAKER
          </span>
          <h1>Messages</h1>
          <p>
            Talk with maintainers, administrators,
            and people who write to you.
          </p>
        </div>
      </section>

      <section className="pageBody">

        {/* API ERROR MESSAGE */}
        {error && (
          <div
            className="msg error"
            role="alert"
            style={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 12,
              padding: 14,
              marginBottom: 16
            }}
          >
            <AlertCircle size={20} />

            <span style={{ flex: 1 }}>
              {error}
            </span>

            {errorAction && (
              <button
                type="button"
                className="btn"
                onClick={retry}
                disabled={loading || threadLoading}
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
                setErrorAction(null);
              }}
            >
              Dismiss
            </button>
          </div>
        )}

        {/* LOADING CONVERSATIONS */}
        {loading && !people && (
          <div className="panel" role="status">
            Loading conversations...
          </div>
        )}

        {/* FAILED INITIAL LOAD */}
        {!loading && !people && (
          <div
            className="panel"
            style={{ padding: 24 }}
          >
            <h3>Unable to load conversations</h3>
            <p>
              The messaging service is temporarily
              unavailable. Please check your connection
              and try again.
            </p>

            <button
              type="button"
              className="btn primary"
              onClick={loadPeople}
            >
              <RefreshCw size={16} />
              Try Again
            </button>
          </div>
        )}

        {/* NO CONVERSATIONS */}
        {!loading &&
          people &&
          people.length === 0 && (
            <div
              className="panel"
              style={{ padding: 24 }}
            >
              <h3>No conversations yet</h3>
              <p>
                Your conversations with contributors,
                maintainers, and administrators
                will appear here.
              </p>

              <button
                type="button"
                className="btn"
                onClick={loadPeople}
              >
                <RefreshCw size={16} />
                Refresh
              </button>
            </div>
          )}

        {/* CONVERSATION LIST AND THREAD */}
        {people && people.length > 0 && (
          <div className="messagesLayout panel">

            <ul
              className="convoList"
              aria-label="Conversations"
            >
              {people.map(person => (
                <li key={person.user_id}>
                  <button
                    type="button"
                    className={
                      'convo' +
                      (active?.user_id === person.user_id
                        ? ' active'
                        : '')
                    }
                    onClick={() => open(person.user_id)}
                    disabled={threadLoading || busy}
                  >
                    <span className="avatar small">
                      {initials(person.name)}
                    </span>

                    <span className="convoText">
                      <strong>
                        {person.name}

                        {person.staff && (
                          <span className="roleBadge">
                            Staff
                          </span>
                        )}
                      </strong>

                      <small>
                        {person.last ||
                          'Start a conversation'}
                      </small>
                    </span>

                    {person.unread > 0 && (
                      <b className="count">
                        {person.unread}
                      </b>
                    )}
                  </button>
                </li>
              ))}
            </ul>

            <div className="thread">

              {/* NO CONVERSATION SELECTED */}
              {!active && !threadLoading && (
                <p className="muted threadEmpty">
                  Select a conversation to read and reply.
                </p>
              )}

              {/* LOADING SELECTED CONVERSATION */}
              {threadLoading && (
                <p role="status" className="muted">
                  Loading messages...
                </p>
              )}

              {/* ACTIVE CONVERSATION */}
              {active && (
                <>
                  <h3 className="threadHead">
                    {active.name}
                  </h3>

                  <div
                    className="bubbles"
                    role="log"
                    aria-live="polite"
                  >
                    {!threadLoading &&
                      thread.length === 0 && (
                        <p className="muted">
                          No messages yet.
                          Say hello below.
                        </p>
                      )}

                    {thread.map(message => (
                      <div
                        key={message.id}
                        className={
                          'bubble' +
                          (message.mine ? ' mine' : '')
                        }
                      >
                        <p>{message.body}</p>

                        <small>
                          {new Date(
                            message.created_at * 1000
                          ).toLocaleString()}
                        </small>
                      </div>
                    ))}

                    <div ref={end} />
                  </div>

                  {/* MESSAGE COMPOSER */}
                  <form
                    className="composer"
                    onSubmit={send}
                  >
                    <input
                      aria-label="Message"
                      value={text}
                      maxLength={2000}
                      onChange={e =>
                        setText(e.target.value)
                      }
                      placeholder="Write a message..."
                      disabled={busy}
                    />

                    <button
                      type="submit"
                      className="btn primary"
                      disabled={
                        busy ||
                        threadLoading ||
                        !text.trim()
                      }
                    >
                      <Send size={16} />
                      {busy ? 'Sending...' : 'Send'}
                    </button>
                  </form>
                </>
              )}
            </div>
          </div>
        )}
      </section>
    </>
  );
}
