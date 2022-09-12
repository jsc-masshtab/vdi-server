import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { FormControl, Validators } from '@angular/forms';
import { WaitService } from '@core/components/wait/wait.service';
import { VmDetailsPopupService } from '../vm-details-popup.service';
import { Subject } from 'rxjs';
import { debounceTime, map } from 'rxjs/operators';

@Component({
  selector: 'vdi-remove-user-vm',
  templateUrl: './remove-user.component.html'
})

export class RemoveUserVmComponent implements OnInit, OnDestroy {

  public isInvalid: boolean = false;
  public isPending: boolean = false;

  public users: any[] = [];
  public usersInput = new FormControl([], Validators.required);

  search = new FormControl('');

  private destroy: Subject<any> = new Subject<any>();

  constructor(
    private waitService: WaitService,
    private service: VmDetailsPopupService,
    public dialog: MatDialog,
    @Inject(MAT_DIALOG_DATA) public data,
    private dialogRef: MatDialogRef<RemoveUserVmComponent>,
  ) {}

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

    this.service.getAssignedUsersFromVm(props).valueChanges.pipe(map((data: any) => data.data['pool']['vm'])).subscribe((res) => {
      this.users = [...res.assigned_users] || []
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

    this.service.freeVmFromUser(this.data.vm.id, data).subscribe((res) => {
      if (res) {
        this.service.getVm().refetch();
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
