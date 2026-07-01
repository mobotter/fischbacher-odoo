/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { SelectCreateDialog } from '@web/views/view_dialogs/select_create_dialog';
import { onMounted, onRendered, onWillUnmount } from '@odoo/owl';

patch(SelectCreateDialog.prototype, {
    setup() {
        super.setup(...arguments);
        this._handleObserver = null;
        this._resize = null;
        onMounted(() => this._initResizeHandle());
        onRendered(() => this._ensureResizeHandle());
        onWillUnmount(() => this._cleanupResizeHandle());
    },

    _initResizeHandle() {
        this._dialogRoot = this.el?.querySelector('.modal-content') || this.el;
        if (!this._dialogRoot) return;

        this._dialogRoot.classList.add('odoo-dialog-resizable');
        this._dialogRoot.style.position = 'relative';
        this._dialogRoot.style.overflow = 'visible';
        this._ensureResizeHandle();

        if (this._handleObserver) this._handleObserver.disconnect();
        this._handleObserver = new MutationObserver(() => this._ensureResizeHandle());
        this._handleObserver.observe(this._dialogRoot, { childList: true, subtree: true });
    },

    _ensureResizeHandle() {
        const root = this._dialogRoot;
        if (!root) return;

        const footer = root.querySelector('.modal-footer') || this._createFooter(root);
        if (footer.querySelector('.odoo-dialog-resize-handle')) return;

        this._resizeHandle = document.createElement('div');
        this._resizeHandle.className = 'odoo-dialog-resize-handle';
        footer.appendChild(this._resizeHandle);

        this._onResizeDown = (ev) => this._startResize(ev);
        this._resizeHandle.addEventListener('pointerdown', this._onResizeDown);
    },

    _createFooter(root) {
        const footer = document.createElement('div');
        footer.className = 'modal-footer odoo-dialog-resize-footer';
        root.appendChild(footer);
        return footer;
    },

    _startResize(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        ev.stopImmediatePropagation?.();

        const r = this._dialogRoot.getBoundingClientRect();
        this._resize = { x: ev.clientX, y: ev.clientY, width: r.width, height: r.height };

        this._onMove = (e) => this._moveResize(e);
        this._onUp = () => this._stopResize();
        document.addEventListener('pointermove', this._onMove);
        document.addEventListener('pointerup', this._onUp);
    },

    _moveResize(ev) {
        if (!this._resize || !this._dialogRoot) return;
        this._dialogRoot.style.width = `${Math.max(420, this._resize.width + (ev.clientX - this._resize.x))}px`;
        this._dialogRoot.style.height = `${Math.max(180, this._resize.height + (ev.clientY - this._resize.y))}px`;
    },

    _stopResize() {
        this._resize = null;
        if (this._onMove) document.removeEventListener('pointermove', this._onMove);
        if (this._onUp) document.removeEventListener('pointerup', this._onUp);
        this._onMove = null;
        this._onUp = null;
    },

    _cleanupResizeHandle() {
        if (this._handleObserver) this._handleObserver.disconnect();
        if (this._resizeHandle && this._onResizeDown) this._resizeHandle.removeEventListener('pointerdown', this._onResizeDown);
        if (this._onMove) document.removeEventListener('pointermove', this._onMove);
        if (this._onUp) document.removeEventListener('pointerup', this._onUp);
    },
});
