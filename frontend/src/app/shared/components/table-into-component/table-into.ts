import { Component,  Input, EventEmitter, Output, ChangeDetectionStrategy } from '@angular/core';
import { Levels } from '@app/shared/enums/levels';

import { ISmtpSettings } from '@pages/settings/smtp/smtp.service';

@Component({
  selector: 'vdi-table-into',
  templateUrl: './table-into.html',
  styleUrls: ['./table-into.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TableIntoComponent  {

  @Input() item: ISmtpSettings | any = {};
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
      console.log(item.level);
      
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
 
  get lvlDescription(): string {
    console.log(this.item.level);
    
    switch (this.item.level) {
      case 0:
        return Levels.All;
      case 1:
        return Levels.Warnings;
      case 2:
        return Levels.Errors; 
      case 4:
        return Levels.Off;
      default:
        return '--';       
    }
  }
}
