import { Component } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'vdi-checkbox-input',
  templateUrl: './checkbox-input.component.html',
  styleUrls: ['./checkbox-input.component.scss'],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      multi: true,
      useExisting: CheckboxInputComponent
    }
  ]
})
export class CheckboxInputComponent implements ControlValueAccessor {
  public value: boolean = false;
  
  public onChange: (value: boolean) => void;
  public writeValue(obj: boolean): void {
    this.value = obj;
  };

  public registerOnChange(fn: any): void {
    this.onChange = fn;
  };

  public registerOnTouched(_fn: any): void { };
 
  setValue() {
    this.value = !this.value;
    this.onChange(this.value)
  }
}

