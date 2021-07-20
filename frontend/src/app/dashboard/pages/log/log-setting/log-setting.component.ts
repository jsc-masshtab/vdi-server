import { Component, OnInit } from '@angular/core';
import { LogSettingService } from './log-setting.service';
import { map } from 'rxjs/operators';
import { FormForEditComponent } from '../../../common/forms-dinamic/change-form/form-edit.component';
import { MatDialog } from '@angular/material/dialog';

@Component({
  selector: 'vdi-log-setting',
  templateUrl: './log-setting.component.html',
  styleUrls: ['./log-setting.component.scss']
})
export class LogSettingComponent implements OnInit {

  item: any;

  collection_period: object[] = [{
    title: 'Тип архивации',
    property: 'by_count',
    type: {
      typeDepend: 'boolean',
      propertyDepend: ['По количеству записей', 'По периоду']
    },
    edit: 'changeByCount'
  },
  {
    title: 'Период архивации',
    property: 'period',
    type: 'string',
    edit: 'changePeriod'
  },
  {
    title: 'Директория архивации',
    property: 'dir_path',
    type: 'string',
    edit: 'changeDirPath'
  }];

  collection_count: object[] = [{
    title: 'Тип архивации',
    property: 'by_count',
    type: {
      typeDepend: 'boolean',
      propertyDepend: ['По количеству записей', 'По периоду']
    },
    edit: 'changeByCount'
  },
  {
    title: 'Количество записей',
    property: 'count',
    type: 'string',
    edit: 'changeCount'
  },
  {
    title: 'Директория архивации',
    property: 'dir_path',
    type: 'string',
    edit: 'changeDirPath'
  }];

  constructor(
    private service: LogSettingService,
    public dialog: MatDialog
  ) { }

  ngOnInit() {
    this.refresh();
  }

  refresh() {
    this.getSettings();
  }

  getSettings() {
    this.service.getSettings().valueChanges.pipe(map(data => data.data.journal_settings))
      .subscribe((data) => {
        this.item = data;
      });
  }

  public actionEdit(method) {
    this[method]();
  }

  // @ts-ignore: Unreachable code error
  private changePeriod(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.service,
          method: 'changeJournalSettings',
          params: {
            ...this.item
          }
        },
        settings: {
          header: 'Изменение периода архивации',
          buttonAction: 'Изменить',
          form: [{
            tag: 'select',
            multiple: false,
            title: 'Выбрать период',
            fieldName: 'period',
            fieldValue: this.item.period,
            data: ['day', 'week', 'month', 'year']
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

  // @ts-ignore: Unreachable code error
  private changeByCount(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.service,
          method: 'changeJournalSettings',
          params: {
            ...this.item
          }
        },
        settings: {
          header: 'Изменение типа архивации',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'checkbox',
            fieldName: 'by_count',
            fieldValue: this.item.by_count,
            description: 'По количеству записей'
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

  // @ts-ignore: Unreachable code error
  private changeCount(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.service,
          method: 'changeJournalSettings',
          params: {
            ...this.item
          }
        },
        settings: {
          header: 'Изменение количества записей',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'text',
            fieldName: 'count',
            fieldValue: this.item.count
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

  // @ts-ignore: Unreachable code error
  private changeDirPath(): void {
    this.dialog.open(FormForEditComponent, {
      disableClose: true,
      width: '500px',
      data: {
        post: {
          service: this.service,
          method: 'changeJournalSettings',
          params: {
            ...this.item
          }
        },
        settings: {
          header: 'Изменение директории архивации',
          buttonAction: 'Изменить',
          form: [{
            tag: 'input',
            type: 'text',
            title: 'Выбрать директорию',
            fieldName: 'dir_path',
            fieldValue: this.item.dir_path
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
}
