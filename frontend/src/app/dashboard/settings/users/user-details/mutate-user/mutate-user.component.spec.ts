/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MutateUserComponent } from './mutate-user.component';

describe('RemoveUserComponent', () => {
  let component: MutateUserComponent;
  let fixture: ComponentFixture<MutateUserComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [MutateUserComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MutateUserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
