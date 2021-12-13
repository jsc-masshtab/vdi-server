import { Component, OnInit } from '@angular/core';
import { MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'tc-remote-messenger',
  templateUrl: './remote-messenger.component.html',
  styleUrls: ['./remote-messenger.component.scss']
})
export class RemoteMessengerComponent implements OnInit {

  constructor(    
    private dialogRef: MatDialogRef<RemoteMessengerComponent>,
    ) { }

  ngOnInit() {
  }


  public close(): void {
    this.dialogRef.close();
  }
  
}
