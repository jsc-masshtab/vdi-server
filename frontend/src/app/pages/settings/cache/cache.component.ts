import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { map } from 'rxjs/operators';

import { FormForEditComponent } from '../../../shared/forms-dinamic/change-form/form-edit.component';
import { CacheService } from './cache.service';
import {YesNoFormComponent} from '@shared/forms-dinamic/yes-no-form/yes-no-form.component';


@Component({
  selector: 'vdi-log-setting',
  templateUrl: './cache.component.html',
  styleUrls: ['./cache.component.scss']
})
export class CacheComponent implements OnInit {

  item: any;

  collection_cache_time: object[] = [
  {
    title: 'Срок хранения данных в кэше',
    property: 'REDIS_EXPIRE_TIME',
    type: 'cache_time',
    edit: 'changeRedisExpireTime'
  }];

  constructor(
    private service: CacheService,
    public dialog: MatDialog
  ) { }

  ngOnInit() {
    this.refresh();
  }

  refresh() {
    this.getSettings();
  }

  getSettings() {
    this.service.getSettings().valueChanges.pipe(map(data => data.data.settings))
      .subscribe((data) => {
        this.item = data;
      });
  }

  public actionEdit(method) {
    this[method]();
  }

  // @ts-ignore: Unreachable code error
  private changeRedisExpireTime(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.service,
          method: 'changeSettings',
          params: {
            ...this.item
          }
        },
        settings: {
          header: 'Изменение срока хранения данных в кэше (сек)',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'text',
            fieldName: 'redis_expire_time',
            fieldValue: this.item.REDIS_EXPIRE_TIME
          }]
        },
        update: {
          method: 'getSettings',
          refetch: true,
          params: {}
        }
      }
    });
  }

  public clearCache() {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '500px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: 'Очистить весь кэш?',
          button: 'Выполнить'
        },
        request: {
          service: this.service,
          action: 'clearCache',
          body: { }
        }
      }
    });
  }
}
