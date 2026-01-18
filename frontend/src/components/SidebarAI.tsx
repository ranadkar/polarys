import { useState, useRef, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useAppDispatch } from '../lib/store';
import { sendMessage, clearChat } from '../lib/chatSlice';
import type { ChatState } from '../lib/chatSlice';
import type { FollowUpSuggestion, ChatMessage } from '../lib/services';
import styles from '../styles/SidebarAI.module.scss';

interface SidebarAIProps {
    onClose?: () => void;
}

// Type for state with chat slice
interface RootStateWithChat {
    search: { query: string; sessionId: string | null };
    chat: ChatState;
}

const SidebarAI = ({ onClose }: SidebarAIProps) => {
    const dispatch = useAppDispatch();
    const chatState = useSelector((state: RootStateWithChat) => state.chat);
    const query = useSelector((state: RootStateWithChat) => state.search.query);
    const messages: ChatMessage[] = chatState?.messages ?? [];
    const status = chatState?.status ?? 'idle';
    const [isOpen, setIsOpen] = useState(false);
    const [inputValue, setInputValue] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Scroll to bottom when messages change
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    // Focus input when opened
    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    const handleToggle = () => {
        setIsOpen(!isOpen);
    };

    const handleClose = () => {
        setIsOpen(false);
        onClose?.();
    };

    const handleSendMessage = (message: string) => {
        if (!message.trim() || status === 'loading') return;
        dispatch(sendMessage(message.trim()));
        setInputValue('');
    };

    const handleFollowUpClick = (followUp: FollowUpSuggestion) => {
        // Show the short version in UI, but send the full version
        handleSendMessage(followUp.full);
    };

    const handleInputSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        handleSendMessage(inputValue);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(inputValue);
        }
    };

    const handleClearChat = () => {
        dispatch(clearChat());
    };

    // Get the last assistant message's follow-ups (max 2)
    const lastAssistantMessage = [...messages].reverse().find(m => m.role === 'assistant');
    const followUps = (lastAssistantMessage?.follow_ups ?? []).slice(0, 2);

    return (
        <>
            {/* Floating Action Button */}
            {!isOpen && (
                <button
                    className={styles.fab}
                    onClick={handleToggle}
                    aria-label="Open AI Assistant"
                >
                    <span className={styles.fabPulse}></span>
                    <span className="material-symbols-outlined">smart_toy</span>
                    <span className={styles.fabLabel}>Ask AI</span>
                </button>
            )}

            {/* Chat Panel */}
            {isOpen && (
                <aside className={styles.sidebar}>
                    {/* Header */}
                    <div className={styles.header}>
                        <div className={styles.headerLeft}>
                            <div className={styles.statusIndicator}>
                                <span className={styles.statusPing}></span>
                                <span className={styles.statusDot}></span>
                            </div>
                            <h3 className={styles.title}>AI Assistant</h3>
                        </div>
                        <div className={styles.headerActions}>
                            {messages.length > 0 && (
                                <button
                                    className={styles.headerBtn}
                                    onClick={handleClearChat}
                                    title="Clear conversation"
                                >
                                    <span className="material-symbols-outlined">delete_sweep</span>
                                </button>
                            )}
                            <button
                                className={styles.headerBtn}
                                onClick={handleClose}
                                title="Close"
                            >
                                <span className="material-symbols-outlined">close</span>
                            </button>
                        </div>
                    </div>

                    {/* Messages Area */}
                    <div className={styles.messagesContainer}>
                        {messages.length === 0 ? (
                            <div className={styles.emptyState}>
                                <div className={styles.emptyIcon}>
                                    <span className="material-symbols-outlined">forum</span>
                                </div>
                                <h4>Ask me anything</h4>
                                <p>I can help you understand the perspectives on "{query}"</p>
                                <div className={styles.starterPrompts}>
                                    <button
                                        className={styles.starterBtn}
                                        onClick={() => handleSendMessage("What are the main perspectives on this topic?")}
                                    >
                                        Main perspectives?
                                    </button>
                                    <button
                                        className={styles.starterBtn}
                                        onClick={() => handleSendMessage("What do conservative sources emphasize?")}
                                    >
                                        Conservative view?
                                    </button>
                                    <button
                                        className={styles.starterBtn}
                                        onClick={() => handleSendMessage("What do liberal sources emphasize?")}
                                    >
                                        Liberal view?
                                    </button>
                                    <button
                                        className={styles.starterBtn}
                                        onClick={() => handleSendMessage("Where do both sides agree?")}
                                    >
                                        Common ground?
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                {messages.map((msg: ChatMessage, index: number) => (
                                    <div
                                        key={index}
                                        className={`${styles.message} ${msg.role === 'user' ? styles.messageUser : styles.messageAssistant}`}
                                    >
                                        {msg.role === 'assistant' && (
                                            <div className={styles.messageAvatar}>
                                                <span className="material-symbols-outlined">smart_toy</span>
                                            </div>
                                        )}
                                        <div className={styles.messageContent}>
                                            {msg.role === 'assistant' && (
                                                <span className={styles.messageLabel}>AI Assistant</span>
                                            )}
                                            <div className={`${styles.messageBubble} ${msg.role === 'user' ? styles.bubbleUser : styles.bubbleAssistant}`}>
                                                <p>{msg.content}</p>
                                            </div>
                                            {msg.role === 'user' && (
                                                <span className={styles.messageTime}>Just now</span>
                                            )}
                                        </div>
                                        {msg.role === 'user' && (
                                            <div className={styles.messageAvatarUser}>
                                                <div className={styles.userGradient}></div>
                                            </div>
                                        )}
                                    </div>
                                ))}

                                {/* Loading indicator */}
                                {status === 'loading' && (
                                    <div className={`${styles.message} ${styles.messageAssistant}`}>
                                        <div className={styles.messageAvatar}>
                                            <span className="material-symbols-outlined">smart_toy</span>
                                        </div>
                                        <div className={styles.messageContent}>
                                            <span className={styles.messageLabel}>AI Assistant</span>
                                            <div className={`${styles.messageBubble} ${styles.bubbleAssistant}`}>
                                                <div className={styles.typingIndicator}>
                                                    <span></span>
                                                    <span></span>
                                                    <span></span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                                <div ref={messagesEndRef} />
                            </>
                        )}
                    </div>

                    {/* Input Area */}
                    <div className={styles.inputArea}>
                        {/* Follow-up suggestions */}
                        {followUps.length > 0 && status !== 'loading' && (
                            <div className={styles.followUps}>
                                {followUps.map((followUp: FollowUpSuggestion, index: number) => (
                                    <button
                                        key={index}
                                        className={styles.followUpBtn}
                                        onClick={() => handleFollowUpClick(followUp)}
                                    >
                                        {followUp.short}
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Text input */}
                        <form className={styles.inputForm} onSubmit={handleInputSubmit}>
                            <textarea
                                ref={inputRef}
                                className={styles.input}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask AI..."
                                disabled={status === 'loading'}
                                rows={1}
                            />
                            <button
                                type="submit"
                                className={styles.sendBtn}
                                disabled={!inputValue.trim() || status === 'loading'}
                            >
                                <span className="material-symbols-outlined">send</span>
                            </button>
                        </form>
                    </div>
                </aside>
            )}
        </>
    );
};

export default SidebarAI;
