import { GroupsService } from '../groups.service';
import { Router } from '@angular/router';
import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Component, OnDestroy, Inject } from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface IData {
  id: string;
  verbose_name: string;
}

@Component({
  selector: 'vdi-remove-group',
  templateUrl: './remove-group.component.html'
})

export class RemoveGroupComponent implements OnDestroy {

  private destroy: Subject<any> = new Subject<any>();

  constructor(private service: GroupsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<RemoveGroupComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData,
              private router: Router) {}


  public send() {
    this.waitService.setWait(true);
    this.service.removeGroup(this.data.id).subscribe((res) => {
      if (res) {
        this.service.getGroups().valueChanges.pipe(takeUntil(this.destroy)).subscribe(() => {
          this.waitService.setWait(false);
          this.dialogRef.close();
          this.router.navigateByUrl('/pages/settings/groups');
        });
      }
    });
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
