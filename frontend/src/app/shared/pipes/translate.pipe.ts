import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'rename',
  pure: true
})
export class TranslatePipe implements PipeTransform {

  constructor() {}

  transform(name) {
    let translate = '';

    if (name === 'FOLDERS_REDIR') {
      translate = 'Общие папки';
    } else if (name === 'SHARED_CLIPBOARD') {
      translate = 'Общий буфер обмена';
    } else if (name === 'USB_REDIR') {
      translate = 'Проброс USB';
    } else if (name === 'LOW') {
      translate = 'Низкий';
    } else if (name === 'MIDDLE') {
      translate = 'Средний';
    } else if (name === 'HIGH') {
      translate = 'Высокий';
    } else  {
      translate = name;
    }
    return translate;
  }
}
