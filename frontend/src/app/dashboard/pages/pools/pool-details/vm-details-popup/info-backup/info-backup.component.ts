import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatDialog } from '@angular/material/dialog';
import { PoolDetailsService } from '../../pool-details.service';
import {YesNoFormComponent} from '../../../../../common/forms-dinamic/yes-no-form/yes-no-form.component';

// interface IData {
//   file_id: string;
// }

@Component({
  selector: 'vdi-info-backup',
  templateUrl: './info-backup.component.html',
  styleUrls: ['./info-backup.component.scss']
})
export class InfoBackupComponent {

  backup: any;

  public collection: any[] = [
    {
      title: 'Название',
      property: 'filename',
      type: 'string'
    },
    {
      title: 'Пул данных',
      property: 'datapool',
      property_lv2: 'verbose_name',
      type: 'string'
    },
    {
      title: 'Тип',
      property: 'assignment_type',
      type: 'string'
    },
    {
      title: 'Размер',
      property: 'size',
      type: 'bites'
    },
    {
      title: 'Статус',
      property: 'status',
      type: 'string'
    }
  ];

  constructor(
    @Inject(MAT_DIALOG_DATA) public data: any,
    private service: PoolDetailsService,
    public dialog: MatDialog
  ) {
    this.backup = data.backup;
  }

  public openRestoreBackup(): void {
    this.dialog.open(YesNoFormComponent, {
      disableClose: true,
      width: '700px',
      data: {
        form: {
          header: 'Подтверждение действия',
          question: 'Восстановить ВМ из резервной копии?',
          button: 'Выполнить'
        },
        request: {
          service: this.service,
          action: 'restoreBackupVm',
          body: {
            vm_id: this.backup.vm_id,
            file_id: this.backup.file_id,
            node_id: this.backup.node.id,
            datapool_id: this.backup.datapool.id
          }
        }
      }
    })
  }
}
