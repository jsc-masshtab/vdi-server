import { Component, OnDestroy, Inject } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { WaitService } from '../../../../core/components/wait/wait.service';
import { GroupsService } from '../groups.service';

@Component({
  selector: 'vdi-remove-group',
  templateUrl: './remove-group.component.html'
})

export class RemoveGroupComponent implements OnDestroy {

  private destroy: Subject<any> = new Subject<any>();

  constructor(
    private service: GroupsService,
    private waitService: WaitService,
    private dialogRef: MatDialogRef<RemoveGroupComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private router: Router
  ) {}

  public send() {
    this.waitService.setWait(true);
    this.service.removeGroup(this.data.id).subscribe((res) => {
      if (res) {
        this.service.getGroups().refetch();
        this.waitService.setWait(false);
        this.dialogRef.close();
        this.router.navigateByUrl('/pages/settings/groups');
      }
    });
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
