import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'rename'
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
    } else  {
      translate = name;
    }
    return translate;
  }
}
