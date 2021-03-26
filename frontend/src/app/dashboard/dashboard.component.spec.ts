import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';

import { DashboardComponent } from './dashboard.component';
import { WebsocketService } from './common/classes/websock.service';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;

  let dialogStub: Partial<MatDialog>;
  let wsStub: Partial<WebsocketService>;

  beforeEach(async(() => {
    wsStub = {
      init() {}
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ DashboardComponent ],
      providers: [
        {
          provide: MatDialog,
          useValue: dialogStub
        },
        {
          provide: WebsocketService,
          useValue: wsStub
        },
      ],
      schemas: [ CUSTOM_ELEMENTS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
