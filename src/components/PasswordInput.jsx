import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export default function PasswordInput({ id, value, onChange, placeholder, autoComplete, invalid, describedBy }) {
  const [show, setShow] = useState(false);
  return <div className="pw">
    <input id={id} type={show ? 'text' : 'password'} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder} autoComplete={autoComplete} aria-invalid={invalid} aria-describedby={describedBy} maxLength={128}/>
    <button type="button" aria-label={show ? 'Hide password' : 'Show password'} aria-pressed={show} onClick={() => setShow(s => !s)}>{show ? <EyeOff size={17}/> : <Eye size={17}/>}</button>
  </div>;
}
