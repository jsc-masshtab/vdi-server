import { Component, OnInit } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';


@Component({
  selector: 'vdi-confirm-modal',
  templateUrl: './confirm-modal.component.html',
  styleUrls: ['./confirm-modal.component.scss']
})
export class ConfirmModalComponent implements OnInit {
  public password: string;
  constructor(public dialogRef: MatDialogRef<ConfirmModalComponent>) { }

  public ngOnInit(): void {
  }

  public onChange(value: string): void {
    this.password = value;
  }

  public close(): void {
    this.dialogRef.close();
  }

  public confirm(): void {
      this.dialogRef.close(this.password);
  }
}
