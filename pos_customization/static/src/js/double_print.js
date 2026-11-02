/** @odoo-module */

import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async printReceipt(...args) {
        if (this._doublePrintInProgress) {
            // Verhindert rekursive Aufrufe
            return super.printReceipt(...args);
        }

        this._doublePrintInProgress = true;

        try {
            // Erster Druckversuch
            const firstPrintPromise = super.printReceipt(...args);
            
            // Warte auf Abschluss oder Timeout (max. 5 Sekunden)
            const timeoutPromise = new Promise((resolve) => {
                setTimeout(() => resolve({ timedOut: true }), 5000);
            });

            const firstResult = await Promise.race([
                firstPrintPromise.then(() => ({ success: true })),
                timeoutPromise
            ]);

            // Kurze Pause, aber nur wenn erster Druck erfolgreich war
            if (firstResult.success) {
                await new Promise((resolve) => setTimeout(resolve, 1000));
                
                // Zweiter Druckversuch
                const secondResult = await super.printReceipt(...args);
                return secondResult;
            }

            // Wenn erster Druck fehlschlug, trotzdem zweiten Versuch machen
            await new Promise((resolve) => setTimeout(resolve, 1000));
            return await super.printReceipt(...args);

        } catch (error) {
            // Fehler loggen, aber nicht werfen, um UI-Flow nicht zu unterbrechen
            console.warn("Belegdruck fehlgeschlagen:", error);
            throw error;
        } finally {
            this._doublePrintInProgress = false;
        }
    },
});
