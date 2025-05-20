import React, { createContext, useContext, useState, useEffect } from 'react';

const DataContext = createContext();

export const DataProvider = ({ children }) => {
    const [data, setData] = useState([]);
    const [invoiceData, setInvoiceData] = useState([]);

    // Add effect to log when data changes
    useEffect(() => {
        console.log("DATA CONTEXT: Project data updated, new length:", data.length);
    }, [data]);

    useEffect(() => {
        console.log("DATA CONTEXT: Invoice data updated, new length:", invoiceData.length);
    }, [invoiceData]);

    // Create enhanced setter functions that log when they're called
    const setDataWithLogging = (newData) => {
        console.log("DATA CONTEXT: setData called with new data, length:", newData.length);
        setData(newData);
    };

    const setInvoiceDataWithLogging = (newData) => {
        console.log("DATA CONTEXT: setInvoiceData called with new data, length:", newData.length);
        setInvoiceData(newData);
    };

    return (
        <DataContext.Provider value={{ 
            data, 
            setData: setDataWithLogging, 
            invoiceData, 
            setInvoiceData: setInvoiceDataWithLogging 
        }}>
            {children}
        </DataContext.Provider>
    );
};

export const useData = () => {
    const context = useContext(DataContext);
    if (!context) {
        throw new Error('useData must be used within a DataProvider');
    }
    return context;
}; 