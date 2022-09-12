import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';
import { FormControl, Validators } from '@angular/forms';

import { WaitService } from '@core/components/wait/wait.service';
import { VmDetailsPopupService } from '../vm-details-popup.service';
import { Subject } from 'rxjs';
import { debounceTime, map } from 'rxjs/operators';

@Component({
  selector: 'vdi-add-user-vm',
  templateUrl: './add-user.component.html'
})

export class AddUserVmComponent implements OnInit, OnDestroy {

  public isInvalid: boolean = false;
  public isPending: boolean = false;

  public users: any[] = [];
  public usersInput = new FormControl([], Validators.required);

  search = new FormControl('');

  private destroy: Subject<any> = new Subject<any>();

  constructor(
    private waitService: WaitService,
    private service: VmDetailsPopupService,
    @Inject(MAT_DIALOG_DATA) public data,
    public dialog: MatDialog,
    private dialogRef: MatDialogRef<AddUserVmComponent>,
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

    this.service.getPossibleUsersFromVm(props).valueChanges.pipe(map((data: any) => data.data['pool']['vm'])).subscribe((res) => {
      this.users = [...res.possible_users] || []
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

    this.service.assignVmToUser(this.data.vm.id, data).subscribe((res) => {
      if (res) {
        this.service.getVm().refetch()
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
