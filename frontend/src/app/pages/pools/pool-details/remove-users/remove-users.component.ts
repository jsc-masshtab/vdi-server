import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { debounceTime, map, takeUntil } from 'rxjs/operators';

import { WaitService } from '../../../../core/components/wait/wait.service';
import { PoolDetailsService } from '../pool-details.service';

interface IData {
  idPool: string;
  namePool: string;
  typePool: string;
  queryset: any;
}

@Component({
  selector: 'vdi-remove-users-pool',
  templateUrl: './remove-users.component.html'
})

export class RemoveUsersPoolComponent  implements OnInit, OnDestroy {

  public isInvalid: boolean = false;
  public isPending: boolean = false;

  public users: any[] = [];
  public usersInput = new FormControl([], Validators.required);

  search = new FormControl('');

  private destroy: Subject<any> = new Subject<any>();

  constructor(
    private waitService: WaitService,
    private poolService: PoolDetailsService,
    private dialogRef: MatDialogRef<RemoveUsersPoolComponent>,
    @Inject(MAT_DIALOG_DATA) public data: IData
  ) { }
  
  ngOnInit() {
    this.load();

    this.search.valueChanges.pipe(
      debounceTime(1000)
    ).subscribe((value) => {
      this.load(value)
    })
  }

  load(value = '') {

    const props = {};

    if (value) {
      props['username'] = value;
    }

    this.isPending = true;

    this.poolService.getAllUsersEntitleToPool(this.data.idPool, props).valueChanges.pipe(map((data: any) => data.data['pool']['users'])).subscribe((res) => {
      this.users = res ? [...res].filter(user => !user.is_superuser) : [];
      this.isPending = false;
    });
  }

  public send() {
    if (!this.usersInput.valid) {
      this.isInvalid = true;
      return;
    }

    const data = this.usersInput.value;

    this.waitService.setWait(true);

    this.poolService.removeUserEntitlementsFromPool(this.data.idPool, data).pipe(takeUntil(this.destroy)).subscribe((res) => {
      if (res) {
        this.poolService.getPool(this.data.idPool, this.data.queryset).refetch();
        this.waitService.setWait(false);
        this.dialogRef.close();
      }
    });
  }

  public selectAll(selected: any[]): void {
    this.usersInput.setValue(selected.map((item: any) => item.id));
  }

  public deselectAll() {
    this.usersInput.setValue([]);
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }
}
