import React, { createContext, useContext, useState, useEffect } from "react";

const WorkbenchContext = createContext();

export function WorkbenchProvider({ children }) {
  const [pinnedItems, setPinnedItems] = useState(() => {
    const saved = localStorage.getItem("biofusion_workbench");
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem("biofusion_workbench", JSON.stringify(pinnedItems));
  }, [pinnedItems]);

  const togglePin = (item) => {
    const exists = pinnedItems.find((p) => p.id === item.id && p.type === item.type);
    if (exists) {
      setPinnedItems(pinnedItems.filter((p) => !(p.id === item.id && p.type === item.type)));
    } else {
      setPinnedItems([...pinnedItems, { ...item, pinnedAt: new Date().toISOString() }]);
    }
  };

  const clearWorkbench = () => setPinnedItems([]);

  const isPinned = (id, type) => pinnedItems.some((p) => p.id === id && p.type === type);

  return (
    <WorkbenchContext.Provider value={{ pinnedItems, togglePin, clearWorkbench, isPinned }}>
      {children}
    </WorkbenchContext.Provider>
  );
}

export function useWorkbench() {
  return useContext(WorkbenchContext);
}
