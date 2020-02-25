import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'vdi-add-select',
  templateUrl: './add-select.html',
  styleUrls: ['./add-select.scss']
})
export class AddSelectComponent {

  public value: string;

  @Output() addValue: EventEmitter<string> = new EventEmitter<string>();

  constructor() {}


  public add() {
    this.addValue.emit(this.value);
    this.value = '';
  }

}

