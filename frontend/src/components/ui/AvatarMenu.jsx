import React, { useState, useRef, useEffect } from 'react';
import { FaUser, FaShieldAlt, FaIdCard, FaGift, FaSignOutAlt, FaLink } from 'react-icons/fa';

const AvatarMenu = ({ user, onLogout }) => {
  const [open, setOpen] = useState(false);
  const menuRef = useRef();

  // Cerrar menú si se hace clic fuera
  useEffect(() => {
    const handler = (e) => {
      if (!menuRef.current?.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="relative" ref={menuRef}>
      {/* Avatar */}
      <img
        src={user?.avatarUrl || '/default-avatar.png'}
        alt="Avatar"
        className="w-10 h-10 rounded-full border-2 border-green-400 cursor-pointer object-cover"
        onClick={() => setOpen(!open)}
      />

      {/* Menú emergente */}
      {open && (
        <div className="absolute bottom-14 left-0 w-64 bg-white rounded-lg shadow-xl border z-50">
          <div className="p-4 border-b">
            <p className="font-semibold text-sm">{user.name}</p>
            <p className="text-xs text-gray-500">{user.email}</p>
          </div>
          <ul className="text-sm divide-y">
            <li className="flex items-center gap-2 p-3 hover:bg-gray-100 cursor-pointer">
              <FaUser /> Profile Page
            </li>
            <li className="flex items-center gap-2 p-3 hover:bg-gray-100 cursor-pointer">
              <FaShieldAlt /> Security
            </li>
            <li className="flex items-center gap-2 p-3 hover:bg-gray-100 cursor-pointer">
              <FaIdCard /> Identification
            </li>
            <li className="flex items-center gap-2 p-3 hover:bg-gray-100 cursor-pointer">
              <FaLink /> Referral
            </li>
            <li className="flex items-center gap-2 p-3 hover:bg-gray-100 cursor-pointer">
              <FaGift /> Reward Center
            </li>
            <li
              className="flex items-center gap-2 p-3 hover:bg-red-100 text-red-500 cursor-pointer"
              onClick={onLogout}
            >
              <FaSignOutAlt /> Signout
            </li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default AvatarMenu;
