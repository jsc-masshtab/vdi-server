import { Component,  Input, EventEmitter, Output } from '@angular/core';
import * as moment from 'moment';

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

  public moment: any;

  constructor() {
    this.moment = moment;
  }

  public actionEditField(method, info = null) {
    this.action.emit(method);
    this.edit.emit(info);
  }

  parseNothing(obj, item) {
    if (obj.property_lv2) {
      return typeof item[obj.property][obj.property_lv2] === 'number' ? 0 : '--'
    } else if (obj.property) {
      return typeof item[obj.property] === 'number' ? 0 : '--'
    } else {
      return '--'
    }
  }
}
