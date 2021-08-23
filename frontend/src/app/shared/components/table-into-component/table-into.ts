import { Component,  Input, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'vdi-table-into',
  templateUrl: './table-into.html',
  styleUrls: ['./table-into.scss']
})
export class TableIntoComponent  {

  @Input() item: {};
  @Input() collection: object[] = [];
  @Output() action: EventEmitter<object> = new EventEmitter<object>();
  @Output() edit: EventEmitter<any> = new EventEmitter<any>();

  constructor() {
   
  }

  public actionEditField(method, info = null) {
    this.action.emit(method);
    this.edit.emit(info);
  }

  parseNothing(obj, item) {
    if (!item) {
      return '--';
    }

    if (obj.property_lv2 && item[obj.property]) {
      return typeof item[obj.property][obj.property_lv2] === 'number' ? 0 : '--';
    }
    if (obj.property) {
      return typeof item[obj.property] === 'number' ? 0 : '--';
    }
    return '--';
  }

  formatBytes(bytes, delimiter = 'Байт', decimals = 3) {
    if (bytes === 0) { return '0 Байт'; }

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Байт', 'Кб', 'Мб', 'Гб', 'Тб', 'Пб', 'Эб', 'Зб', 'Йб'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const def = sizes.findIndex(size => size === delimiter);

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i + def];
  }
}
